from flask import abort, jsonify

from flask_restful import Resource

from app import cfg, util


class StatsResource(Resource):
    def get(self):
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


class ServerStatsResource(Resource):
    def get(self, id):
        if not util.get_server(id):
            return abort(404)

        try:
            return jsonify(util.fetch_server_status(id))
        except Exception as E:
            return jsonify({"error": str(E)})


class StatsTotalsResource(Resource):
    def get(self):
        try:
            return jsonify(util.fetch_server_totals())
        except Exception as E:
            return jsonify({"error": str(E)})
