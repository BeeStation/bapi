from bapi import cfg
from bapi import db
from bapi import util
from bapi.patreon_api import exchange_oauth_code
from bapi.patreon_api import get_identity_id
from bapi.patreon_api import PatreonAPIError
from bapi.schemas import APIPasswordRequiredSchema
from bapi.schemas import BudgetSchema
from bapi.schemas import PatreonLinkSchema
from flask import current_app
from flask import jsonify
from flask import redirect
from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint

blp = Blueprint("patreon", "patreon", url_prefix="/")


@blp.route("/patreonauth")
class PatreonOAuthResource(MethodView):
    @blp.doc(description="Patreon oauth callback.")
    def get(self):
        code = request.args.get("code")
        ckey = request.args.get("state")

        if code is not None and ckey is not None:
            try:
                access_token = exchange_oauth_code(
                    cfg.PRIVATE["patreon"]["client_id"],
                    cfg.PRIVATE["patreon"]["client_secret"],
                    code,
                    f"{cfg.API['api-url']}/patreonauth",
                )
                user_id = get_identity_id(access_token)
            except PatreonAPIError as error:
                current_app.logger.error(f"Patreon OAuth failed: {error}")
                return redirect(f"{cfg.API['website-url']}/linkpatreon?error=unknown")

            player = db.Player.from_ckey(ckey)

            if not player:
                return redirect(f"{cfg.API['website-url']}/linkpatreon?error=invalidckey")

            db.Patreon.link(ckey, user_id)

            return redirect(f"{cfg.API['website-url']}/linkpatreon?success=true")

        else:
            return redirect(f"{cfg.API['website-url']}/linkpatreon?error=unknown")


@blp.route("/linked_patreons")
class LinkedPatreonListResource(MethodView):
    @blp.response(200, PatreonLinkSchema(many=True))
    @blp.arguments(APIPasswordRequiredSchema, location="query")
    @blp.doc(description="Get a list of linked ckey-Patreon accounts.")
    def get(self, args):
        if args.get("api_pass") == cfg.PRIVATE["api_passwd"]:
            try:
                links = db.db_session.query(db.Patreon).all()
                return jsonify([{"ckey": link.ckey, "patreon_id": link.patreon_id} for link in links])
            except Exception as e:
                current_app.logger.error(f"database error while fetching linked Patrons: {e}")
                return jsonify({"error": "database error"}), 500
        else:
            return jsonify({"error": "bad pass"}), 401


@blp.route("/budget")
class BudgetResource(MethodView):
    @blp.response(200, BudgetSchema)
    @blp.doc(description="Get Patreon donation goal information.")
    def get(self):
        try:
            income = util.get_patreon_income()
        except PatreonAPIError as error:
            current_app.logger.error(f"failed to fetch Patreon campaign income: {error}")
            return jsonify({"error": "Patreon API unavailable"}), 502

        current_goal = min(
            [goal for goal in cfg.API["patreon-goals"] if goal > income] or (max(cfg.API["patreon-goals"]),)
        )  # Find the lowest goal we haven't passed

        return {
            "income": round(income / 100, 2),
            "goal": round(current_goal / 100, 2),
            "percent": int(income / current_goal * 100),
        }
