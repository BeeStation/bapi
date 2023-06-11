import patreon
from flask import jsonify, redirect, request
from flask_apispec import MethodResource, doc, marshal_with, use_kwargs
from flask_restful import Resource
from marshmallow import Schema, fields

from bapi import cfg, db, ma_ext, util
from bapi.schemas import *


class PatreonOuathResource(MethodResource):
    @doc(description="Patreon oauth callback.")
    def get(self):
        code = request.args.get("code")
        ckey = request.args.get("state")

        if code is not None and ckey is not None:
            oauth_client = patreon.OAuth(cfg.PRIVATE["patreon"]["client_id"], cfg.PRIVATE["patreon"]["client_secret"])

            tokens = oauth_client.get_tokens(code, f"{cfg.API['api-url']}/patreonauth")

            if "error" in tokens:
                raise Exception(tokens["error"])

            access_token = tokens["access_token"]
            api_client = patreon.API(access_token)
            user_identity = api_client.get_identity().data()
            user_id = user_identity.id()
            player = db.Player.from_ckey(ckey)

            if not player:
                return redirect(f"{cfg.API['website-url']}/linkpatreon?error=invalidckey")

            db.Patreon.link(ckey, user_id)

            return redirect(f"{cfg.API['website-url']}/linkpatreon?success=true")

        else:
            return redirect(f"{cfg.API['website-url']}/linkpatreon?error=unknown")


class PatreonLinkSchema(Schema):
    ckey = fields.String()
    patreon_id = fields.String()


class LinkedPatreonListResource(MethodResource):
    @marshal_with(PatreonLinkSchema(many=True))
    @use_kwargs(APIPasswordRequiredSchema)
    @doc(description="Get a list of linked ckey-Patreon accounts.")
    def get(self, **kwargs):
        if kwargs["api_pass"] == cfg.PRIVATE["api_passwd"]:
            try:
                links = db.db_session.query(db.Patreon).all()
                return jsonify([{"ckey": link.ckey, "patreon_id": link.patreon_id} for link in links])
            except Exception as E:
                return jsonify({"error": str(E)})
        else:
            return jsonify({"error": "bad pass"})


class BudgetSchema(Schema):
    income = fields.Integer()
    goal = fields.Integer()
    percent = fields.Integer()


class BudgetResource(MethodResource):
    @marshal_with(BudgetSchema)
    @doc(description="Get Patreon donation goal information.")
    def get(self):
        income = util.get_patreon_income()

        current_goal = min(
            [goal for goal in cfg.API["patreon-goals"] if goal > income] or (max(cfg.API["patreon-goals"]),)
        )  # Find the lowest goal we haven't passed

        return {
            "income": round(income / 100, 2),
            "goal": round(current_goal / 100, 2),
            "percent": int(income / current_goal * 100),
        }
