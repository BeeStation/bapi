from app import cfg
from app import db
from app import util

from flask import Blueprint, abort, jsonify

bp_stats = Blueprint('stats', __name__)

@bp_stats.route("/stats")
def page_stats():
	try:
		d = {}

		for server in cfg.SERVERS:
			if server["open"]:
				try:
					d[server["id"]] = util.fetch_server_status(server["id"])
				except Exception as E:
					d[server["id"]] = {"error": str(E)}

		return jsonify(d)

	except Exception as E:
		return jsonify({"error": str(E)})


@bp_stats.route("/stats/<string:id>")
def page_stats_server(id):
	if not util.get_server(id):
		return abort(404)

	try:
		return jsonify(util.fetch_server_status(id))
	except Exception as E:
		return jsonify({"error": str(E)})


@bp_stats.route("/stats/totals")
def page_stats_totals():
	try:
		return jsonify(util.fetch_server_totals())
	except Exception as E:
		return jsonify({"error": str(E)})

