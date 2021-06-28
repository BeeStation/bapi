from app import cfg
from app import db
from app import util

from flask import abort
from flask import Blueprint
from flask import jsonify
from flask import request

bp_general = Blueprint('general', __name__)

@bp_general.route("/version")
def page_version():
	return cfg.VERSION

@bp_general.route("/playerlist")
def page_playerlist():
	try:
		d = {}

		for server in cfg.SERVERS:
			if server["open"]:
				try:
					d[server["id"]] = util.fetch_server_players(server["id"])
				except Exception as E:
					d[server["id"]] = {"error": str(E)}

		return jsonify(d)

	except Exception as E:
		return jsonify({"error": str(E)})


@bp_general.route("/playerlist/<string:id>")
def page_playerlist_server(id):
	if not util.get_server(id):
		return abort(404)

	try:
		return jsonify(util.fetch_server_players(id))
	except Exception as E:
		return jsonify({"error": str(E)})


@bp_general.route("/servers")
def page_servers():
	try:
		return jsonify(cfg.SERVERS)
	except Exception as E:
		return jsonify({"error": str(E)})