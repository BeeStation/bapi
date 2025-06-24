import secrets

import discordoauth2
from bapi import cfg
from bapi import db
from flask import jsonify
from flask import redirect
from flask import request
from flask import session
from flask_apispec import doc
from flask_apispec import MethodResource

discord_client = discordoauth2.Client(
    cfg.PRIVATE["discord"]["client_id"],
    secret=cfg.PRIVATE["discord"]["client_secret"],
    redirect=f"{cfg.API['api-url']}/discord/callback",
)


class DiscordOauthRequestResource(MethodResource):
    @doc(description=("Discord oauth initiator"))
    def get(self):
        ip = request.args.get("ip")
        if isinstance(ip, str) and ip.isdigit():
            ip = int(ip)
        if not isinstance(ip, int) or ip > 4294967296 or ip < 0:  # 2^32 (max IPv4 int)
            return jsonify(
                {"error": "must provide IP address. must be a valid numerical representation of an IPv4 address."}
            )
        session["oauth2_state"] = f"{ip},{secrets.token_urlsafe(16)}"
        return redirect(discord_client.generate_uri(scope=["identify"], state=session["oauth2_state"]))


class DiscordOuathResource(MethodResource):
    @doc(description="Discord oauth callback.")
    def get(self):
        code = request.args.get("code")
        state = request.args.get("state")

        if code is None:
            return jsonify({"error": "bad oauth code"})

        state_session = session.get("oauth2_state")
        if state is None or state_session is None or state != state_session:
            return jsonify({"error": "bad state"})  # let's not keep this around
        del session["oauth2_state"]

        ip = int(state.split(",")[0])
        discord_uid = None
        discord_username = None

        try:
            access = discord_client.exchange_code(code)
            identify = access.fetch_identify()
            discord_uid = identify["id"]
            discord_username = identify["username"]
            discriminator = identify["discriminator"]
            # Handle non-unique usernames
            if discriminator != "0":
                discord_username = f"{discord_username}#{discriminator}"
        except KeyError | discordoauth2.exceptions.Exceptions:
            return jsonify({"error": "error authorizing with Discord"})
        if discord_uid is None or discord_username is None:
            return jsonify({"error": "error authorizing with Discord"})
        db.Session.create_session(ip, "discord", discord_uid, discord_username, cfg.API["game-session-duration"])
