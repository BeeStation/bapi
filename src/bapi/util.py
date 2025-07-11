import json
import re
import secrets
import socket
import struct
from random import choice as randchoice

import requests
from bapi import cfg
from bapi import db
from cachetools import cached
from cachetools import TTLCache


def generate_random_session_token():
    return secrets.token_hex(64)


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


# flake8: noqa: E501
@cached(cache=TTLCache(ttl=21600, maxsize=1))
def get_patreon_income():
    try:
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15"
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15",
        ]
        # Due to a recent change on Patreon's side, we need to pick a random user-agent to actually complete the request.
        headers = {"User-Agent": randchoice(user_agents)}
        data = requests.get("https://www.patreon.com/api/campaigns/1671674", timeout=2, headers=headers).json()["data"][
            "attributes"
        ]

        pledge_sum = data["campaign_pledge_sum"]

        return pledge_sum

    except:  # noqa: E722
        return 0  # noqa: E722
