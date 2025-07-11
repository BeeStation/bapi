from bapi import cfg
from bapi import util
from bapi.schemas import StatsTotalsSchema
from flask import current_app
from flask import jsonify
from flask.views import MethodView
from flask_smorest import Blueprint


blp = Blueprint("stats", "stats", url_prefix="/stats")


@blp.route("/")
class StatsResource(MethodView):
    @blp.doc(description="Returns the JSON data from the ?status game query of all servers.")
    def get(self):
        try:
            d = {}

            for server in cfg.SERVERS:
                if server["open"]:
                    try:
                        d[server["id"]] = util.fetch_server_status(server["id"])
                    except Exception as e:
                        current_app.logger.error(f"error while fetching server stats for {server['id']}: {e}")
                        d[server["id"]] = {"error": "could not retrieve server stats"}

            return jsonify(d)

        except TimeoutError:
            return jsonify({"error": "timed out"}), 504
        except Exception as e:
            current_app.logger.error(f"error while fetching server stats: {e}")
            return jsonify({"error": "could not retrieve server stats"}), 500


@blp.route("/<string:id>")
class ServerStatsResource(MethodView):
    @blp.doc(description="Returns the JSON data from the ?status game query of the specified server.")
    def get(self, id):
        if not util.get_server(id):
            return jsonify({"error": "unknown server"}), 404

        try:
            return jsonify(util.fetch_server_status(id))
        except TimeoutError:
            return jsonify({"error": "timed out"}), 504
        except Exception as e:
            current_app.logger.error(f"error while fetching server stats for {id}: {e}")
            return jsonify({"error": "could not retrieve server stats"}), 500


@blp.route("/totals")
class StatsTotalsResource(MethodView):
    @blp.doc(description="Returns total unique players, total rounds, and total connections.")
    @blp.response(200, StatsTotalsSchema)
    def get(self):
        return util.fetch_server_totals()
