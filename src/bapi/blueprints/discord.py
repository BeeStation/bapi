import ipaddress
import re
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
    ip_str = None
    if not isinstance(ip, str):
        return jsonify({"error": "provided IP address invalid"}), 400
    try:
        ip_str = ip
        ip = ipaddress.ip_address(ip)
    except ValueError:
        return jsonify({"error": "provided IP address invalid"}), 400
    if "," in ip_str:
        return jsonify({"error": "provided IP address invalid"}), 400
    if ip.version == 6:
        return jsonify({"error": "IPv6 address not allowed"}), 400
    if ip.is_multicast or ip.is_unspecified:
        return jsonify({"error": "multicast or unspecified address not allowed"}), 400
    seeker_port = request.args.get("seeker_port")
    if not isinstance(seeker_port, str) or not re.match("^[0-9]+$", seeker_port):
        seeker_port = ""
    try:
        seeker_port = int(seeker_port)
    except ValueError:
        seeker_port = ""
    if not isinstance(seeker_port, int) or seeker_port > 65535 or seeker_port < 1023:
        seeker_port = ""
    nonce = request.args.get("nonce")
    if not isinstance(nonce, str) or len(nonce) != 64 or not re.match("^[a-z0-9]+$", nonce):
        return jsonify({"error": "bad nonce"}), 400
    session["oauth2_state"] = (
        f"{urllib.parse.quote(ip_str, safe="", encoding="utf-8")},{seeker_port},{nonce},{secrets.token_urlsafe(16)}"
    )
    return redirect(discord_client.generate_uri(scope=["identify"], state=session["oauth2_state"]))


@discord_blueprint.route("/callback", methods=["GET"])
def discord_callback():
    code = request.args.get("code")
    state = request.args.get("state")

    if code is None:
        return jsonify({"error": "bad oauth code"}), 400

    state_session = session.get("oauth2_state")
    if state is None or state_session is None or state != state_session:
        return jsonify({"error": "bad state"}), 400  # let's not keep this around
    del session["oauth2_state"]

    state_attrs = state.split(",")
    if len(state_attrs) != 4:
        return jsonify({"error": "bad state"}), 400
    ip = urllib.parse.unquote(state_attrs[0])
    seeker_port = state_attrs[1]
    nonce = state_attrs[2]
    if not isinstance(nonce, str) or len(nonce) != 64 or not re.match("^[a-z0-9]+$", nonce):
        return jsonify({"error": "bad state"}), 400
    nonce_duration = cfg.API.get("nonce-valid-duration")
    if nonce_duration is None:
        nonce_duration = 240
    try:
        nonce_valid, reason_invalid = db.SessionCreationNonce.is_valid_session_creation(
            ip, seeker_port, nonce, nonce_duration
        )
        if not nonce_valid:
            notice = ""
            if reason_invalid == "invalid":
                notice = " account security risk: check if connected to a genuine BeeStation game server."
            elif reason_invalid == "expired":
                notice = " log in within a shorter time period."
            return jsonify({"error": f"{reason_invalid or "invalid"} nonce.{notice}"}), 401
    except Exception as e:
        current_app.logger.error(f"error while checking nonce: {e}")
        return jsonify({"error": "error checking nonce"}), 500

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
        return jsonify({"error": "error creating session"}), 500
