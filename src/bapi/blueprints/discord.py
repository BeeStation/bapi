import ipaddress
import secrets
import urllib.parse

from bapi import cfg
from bapi import db
from discordoauth2 import Client as DiscordClient
from discordoauth2.exceptions import Exceptions
from flask import Blueprint
from flask import current_app
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import request
from flask import session

discord_blueprint = Blueprint("discord", __name__, template_folder="templates", url_prefix="/discord")

discord_client = DiscordClient(
    cfg.PRIVATE["discord"]["client_id"],
    secret=cfg.PRIVATE["discord"]["client_secret"],
    redirect=f"{cfg.API['api-url']}/discord/callback",
)


@discord_blueprint.route("/auth", methods=["GET"])
def discord_auth():
    ip = request.args.get("ip")
    if not isinstance(ip, str):
        return jsonify({"error": "provided IP address invalid"})
    try:
        ip = ipaddress.ip_address(ip)
    except ValueError:
        return jsonify({"error": "provided IP address invalid"})
    if ip.version == 6:
        return jsonify({"error": "IPv6 address not allowed"})
    if ip.is_multicast or ip.is_unspecified:
        return jsonify({"error": "multicast or unspecified address not allowed"})
    seeker_port = request.args.get("seeker_port")
    if not isinstance(seeker_port, str) or not seeker_port.isdigit():
        seeker_port = ""
    try:
        seeker_port = int(seeker_port)
    except ValueError:
        seeker_port = ""
    if not isinstance(seeker_port, int) or seeker_port > 65535 or seeker_port < 1023:
        seeker_port = ""
    session["oauth2_state"] = (
        f"{urllib.parse.quote(ip.exploded, safe="", encoding="utf-8")},{seeker_port},{secrets.token_urlsafe(16)}"
    )
    return redirect(discord_client.generate_uri(scope=["identify"], state=session["oauth2_state"]))


@discord_blueprint.route("/callback", methods=["GET"])
def discord_callback():
    code = request.args.get("code")
    state = request.args.get("state")

    if code is None:
        return jsonify({"error": "bad oauth code"})

    state_session = session.get("oauth2_state")
    if state is None or state_session is None or state != state_session:
        return jsonify({"error": "bad state"})  # let's not keep this around
    del session["oauth2_state"]

    state_attrs = state.split(",")
    ip = urllib.parse.unquote(state_attrs[0])
    seeker_port = state_attrs[1]
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
    except Exceptions.RateLimited as e:
        return jsonify({"error": "too many requests", "retry_after": e.retry_after}), 429
    except Exceptions.Forbidden as e:
        current_app.logger.error(f"Forbidden exception during Discord authorization: {e}")
        return (
            jsonify(
                {"error": "error authorizing with Discord (invalid OAuth scopes, this is a server configuration error)"}
            ),
            500,
        )
    except Exceptions.HTTPException as e:
        if f"{e}".startswith("the code"):  # provide a more useful message to the user
            return jsonify({"error": "error authorizing with Discord (invalid/expired OAuth code)"}), 400
        current_app.logger.error(f"HTTPException occurred during Discord authorization: {e}")
        return jsonify({"error": "error authorizing with Discord"}), 500
    except KeyError:
        return jsonify({"error": "error authorizing with Discord (no data)"}), 400
    if discord_uid is None or discord_username is None:
        return jsonify({"error": "error authorizing with Discord (no data)"}), 400
    session_duration = cfg.API.get("game-session-duration")
    if session_duration is None:
        session_duration = 90
    token = db.Session.create_session(ip, "discord", discord_uid, discord_username, session_duration)
    if token is not None:
        return render_template("token.html", token=token, token_duration=session_duration, seeker_port=seeker_port)
    else:
        return jsonify({"error": "error creating session"})
