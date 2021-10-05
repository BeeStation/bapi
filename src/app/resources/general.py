from app import cfg, util
from flask import abort, jsonify
from flask_restful import Resource


class VersionResource(Resource):
    def get(self):
        return cfg.VERSION


class PlayerListResource(Resource):
    def get(self):
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


class ServerPlayerListResource(Resource):
    def get(self, id):
        if not util.get_server(id):
            return abort(404)

        try:
            return jsonify(util.fetch_server_players(id))
        except Exception as E:
            return jsonify({"error": str(E)})


class ServerListResource(Resource):
    def get(self):
        try:
            return jsonify(cfg.SERVERS)
        except Exception as E:
            return jsonify({"error": str(E)})
