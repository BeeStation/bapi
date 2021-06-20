from app import cfg
from app import db
from app import util

from flask import Blueprint, jsonify, redirect, request

import patreon

bp_patreon = Blueprint('patreon', __name__)

@bp_patreon.route("/patreonauth")
def page_patreon_oauth():

	try:
		code = request.args.get('code')
		ckey = request.args.get('state')

		if code != None and ckey != None:
			oauth_client = patreon.OAuth(cfg.PRIVATE["patreon"]["client_id"], cfg.PRIVATE["patreon"]["client_secret"])

			tokens = oauth_client.get_tokens(code, f"{cfg.API['website-url']}/patreonauth")

			access_token = tokens['access_token']

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

	except Exception as E:
		return str(E)
	
	return redirect(f"{cfg.API['website-url']}/linkpatreon?error=unknown")


@bp_patreon.route("/linked_patreons")
def page_api_get_linked_patreons():
	if request.args.get("pass") == cfg.PRIVATE["api_passwd"]:
		try:
			links = db.db_session.query(db.Patreon).all()
			return jsonify([{"ckey": link.ckey, "patreon_id": link.patreon_id} for link in links])
		except Exception as E:
			return jsonify({"error": str(E)})
	else:
		return jsonify({"error": "bad pass"})


@bp_patreon.route("/budget")
def page_api_budget():
	income = util.get_patreon_income()

	current_goal = min([goal for goal in cfg.API['patreon-goals'] if goal > income] or (max(cfg.API['patreon-goals']),)) # Find the lowest goal we haven't passed

	budget_stats = {
		"income": round(income/100, 2),
		"goal": round(current_goal/100, 2),
		"percent": int(income/current_goal*100)
	}
	return jsonify(budget_stats)