from flask import abort, jsonify
from flask_apispec import MethodResource, use_kwargs, marshal_with, doc
from flask_restful import Resource
from marshmallow import schema, fields

from app import cfg, util


class VersionResource(Resource):
    @doc(description="Get the current version of the API.")
    def get(self):
        return cfg.VERSION


class PlayerListResource(Resource):
    @doc(description="Get a list of currently playing CKEYs on all servers.")
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
    @doc(description="Get a list of currently playing CKEYs on a specific server.")
    def get(self, id):
        if not util.get_server(id):
            return abort(404)

        try:
            return jsonify(util.fetch_server_players(id))
        except Exception as E:
            return jsonify({"error": str(E)})


class ServerListResource(Resource):
    @doc(description="Get a list of the manifest details of all servers.")
    def get(self):
        return jsonify(cfg.SERVERS)
