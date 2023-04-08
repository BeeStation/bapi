import json
import re
import socket
import struct

import requests
from cachetools import TTLCache, cached

from app import cfg, db


def to_ckey(byondkey):
    return re.sub(r"[^a-zA-Z0-9]", "", byondkey).lower()


def get_server(id):
    for server in cfg.SERVERS:
        if server["id"] == id:
            return server


def get_server_from_alias(alias):
    for server in cfg.SERVERS:
        if alias in server["aliases"] or alias == server["id"]:
            return server


def get_server_default():
    return cfg.SERVERS[0]


def topic_query(addr, port, query, auth="anonymous"):
    query_str = json.dumps({"query": query, "auth": auth, "source": cfg.API["request-source"]})

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    query = b"\x00\x83" + struct.pack(">H", len(query_str) + 6) + b"\x00\x00\x00\x00\x00" + query_str.encode() + b"\x00"
    sock.settimeout(0.5)
    sock.connect((addr, port))

    sock.sendall(query)

    data = sock.recv(4096)

    parsed_data = json.loads(data[5:-1].decode())

    return parsed_data


def topic_query_server(id, query, auth="anonymous"):
    server = get_server(id)

    return topic_query(server["host"], server["port"], query, auth)


@cached(cache=TTLCache(ttl=5, maxsize=10))
def fetch_server_status(id):
    d = topic_query_server(id, "status")

    if d["statuscode"] == 200:
        return d["data"]
    else:
        return d


@cached(cache=TTLCache(ttl=5, maxsize=10))
def fetch_server_players(id):
    d = topic_query_server(id, "playerlist")

    if d["statuscode"] == 200:
        return d["data"]
    else:
        return d


@cached(cache=TTLCache(ttl=10, maxsize=10))
def fetch_server_totals():
    d = {}
    d["total_players"] = db.db_session.query(db.Player).count()
    d["total_rounds"] = db.db_session.query(db.Round).count()
    d["total_connections"] = db.db_session.query(db.Connection).count()

    return d


@cached(cache=TTLCache(ttl=21600, maxsize=1))
def get_patreon_income():
    try:
        data = requests.get("https://www.patreon.com/api/campaigns/1671674", timeout=2).json()["data"]["attributes"]

        pledge_sum = data["campaign_pledge_sum"]

        return pledge_sum

    except:
        return 0
