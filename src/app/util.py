from app import cfg
from app import db

from cachetools import cached
from cachetools import TTLCache

import re
import requests

import socket
import struct

import urllib.parse

def to_ckey(byondkey):
	return re.sub(r'[^a-zA-Z0-9]', '', byondkey).lower()


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


def topic_query(addr, port, querystr):

	if querystr[0] != "?":
		querystr = "?"+querystr
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	query = b"\x00\x83" + struct.pack('>H', len(querystr) + 6) + b"\x00\x00\x00\x00\x00" + querystr.encode() + b"\x00"
	sock.settimeout(3)
	sock.connect((addr, port))

	sock.sendall(query)

	data = sock.recv(4096)

	parsed_data = urllib.parse.parse_qs(data[5:-1].decode(), keep_blank_values=True)
	return {i:parsed_data[i][0] for i in parsed_data.keys()}


@cached(cache=TTLCache(ttl=1, maxsize=10))
def topic_query_server(id, query, args=None):
	server = get_server(id)

	return topic_query(server["host"],server["port"], query + "&" + urllib.parse.urlencode(args) if args else query)


@cached(cache=TTLCache(ttl=5, maxsize=10))
def fetch_server_status(id):
	try:
		d = topic_query_server(id, "status")
		d["admins"] = int(d["admins"])
		d["ai"] = bool(d["ai"])
		d["enter"] = bool(d["enter"])
		d["extreme_popcap"] = int(d["extreme_popcap"])
		d["gamestate"] = int(d["gamestate"])
		d["players"] = int(d["players"])
		d["popcap"] = int(d["popcap"])
		d["respawn"] = bool(d["respawn"])
		d["round_duration"] = int(d["round_duration"])
		d["round_id"] = int(d["round_id"])
		d["soft_popcap"] = int(d["soft_popcap"])
		d["shuttle_timer"] = int(d["shuttle_timer"])
		d["vote"] = bool(d["vote"])
	except Exception as E:
		return {"error": str(E)}

	return d


@cached(cache=TTLCache(ttl=5, maxsize=10))
def fetch_server_players(id):
	try:
		d = list(topic_query_server(id, "playerlist"))
	except Exception as E:
		return {"error": str(E)}

	return d


@cached(cache=TTLCache(ttl=10, maxsize=10))
def fetch_server_totals():
	d = {}
	d["total_players"] = db.db_session.query(db.Player).count()
	d["total_rounds"] = db.db_session.query(db.Round).count()
	d["total_connections"] = db.db_session.query(db.Connection).count()

	return d


@cached(cache=TTLCache(ttl=30, maxsize=1))
def get_patreon_income():
	try:
		data = requests.get("https://www.patreon.com/api/campaigns/1671674", timeout=2).json()["data"]["attributes"]

		pledge_sum = data["campaign_pledge_sum"]
		
		return pledge_sum
		
	except:
		return 0
