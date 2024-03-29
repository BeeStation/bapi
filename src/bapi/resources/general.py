from bapi import cfg
from bapi import util
from bapi.schemas import APIPasswordRequiredSchema
from flask import abort
from flask import jsonify
from flask_apispec import doc
from flask_apispec import MethodResource
from flask_apispec import use_kwargs


class VersionResource(MethodResource):
    @doc(description="Get the current version of the API.")
    def get(self):
        return cfg.VERSION


class PlayerListResource(MethodResource):
    @use_kwargs(APIPasswordRequiredSchema)
    @doc(description="Get a list of currently playing CKEYs on all servers.")
    def get(self, api_pass):
        if api_pass == cfg.PRIVATE["api_passwd"]:
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
        else:
            return jsonify({"error": "bad pass"})


class ServerPlayerListResource(MethodResource):
    @use_kwargs(APIPasswordRequiredSchema)
    @doc(description="Get a list of currently playing CKEYs on a specific server.")
    def get(self, id, api_pass):
        if api_pass == cfg.PRIVATE["api_passwd"]:
            if not util.get_server(id):
                return abort(404, {"error": "unknown server"})

            try:
                return jsonify(util.fetch_server_players(id))
            except Exception as E:
                return jsonify({"error": str(E)})
        else:
            return jsonify({"error": "bad pass"})


class ServerListResource(MethodResource):
    @doc(description="Get a list of the manifest details of all servers.")
    def get(self):
        return jsonify(cfg.SERVERS)
