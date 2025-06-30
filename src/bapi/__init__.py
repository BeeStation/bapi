import secrets
from os import environ

from bapi import cfg
from flask import Flask
from flask import redirect
from flask_cors import CORS
from flask_smorest import Api
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Setup the ability to store session data (this is solely used for OAuth states)
app.secret_key = secrets.token_urlsafe(32)

if environ.get("DEBUG") == "True":
    from werkzeug.debug import DebuggedApplication

    app.wsgi_app = DebuggedApplication(app.wsgi_app, True)

    app.debug = True

if environ.get("APM") == "True":
    from elasticapm.contrib.flask import ElasticAPM

    apm_url = "http://0.0.0.0:8200"
    apm_debug = "False"
    apm_token = ""

    # Check for APM environ variables
    if "APM_URL" in environ:
        apm_url = environ["APM_URL"]
    if "APM_DEBUG" in environ:
        apm_debug = environ["APM_DEBUG"]
    if "APM_TOKEN" in environ:
        apm_token = environ["APM_TOKEN"]

    app.config["ELASTIC_APM"] = {
        # Set required service name. Allowed characters:
        # a-z, A-Z, 0-9, -, _, and space
        "SERVICE_NAME": "bapi",
        # Use if APM Server requires a token
        "SECRET_TOKEN": apm_token,
        # Set custom APM Server URL (default: http://0.0.0.0:8200)
        "SERVER_URL": apm_url,
        "DEBUG": bool(apm_debug),
    }

    apm = ElasticAPM(app)

app.config["API_TITLE"] = "BeeStation API"
app.config["API_VERSION"] = "v2"
app.config["OPENAPI_VERSION"] = "3.1.1"
app.config["OPENAPI_URL_PREFIX"] = ""
app.config["OPENAPI_JSON_PATH"] = "/docs_json"
app.config["OPENAPI_SWAGGER_UI_PATH"] = "/docs"
app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.25.3/"

app.url_map.strict_slashes = False

cors = CORS(app, resources={r"*": {"origins": "*"}})


app.config["SQLALCHEMY_BINDS"] = {
    "game": "mysql://{username}:{password}@{host}:{port}/{db}".format(
        username=cfg.PRIVATE["database"]["game"]["user"],
        password=cfg.PRIVATE["database"]["game"]["pass"],
        host=cfg.PRIVATE["database"]["game"]["host"],
        port=cfg.PRIVATE["database"]["game"]["port"],
        db=cfg.PRIVATE["database"]["game"]["db"],
    ),
    "session": "mysql://{username}:{password}@{host}:{port}/{db}".format(
        username=cfg.PRIVATE["database"]["session"]["user"],
        password=cfg.PRIVATE["database"]["session"]["pass"],
        host=cfg.PRIVATE["database"]["session"]["host"],
        port=cfg.PRIVATE["database"]["session"]["port"],
        db=cfg.PRIVATE["database"]["session"]["db"],
    ),
    "site": "mysql://{username}:{password}@{host}:{port}/{db}".format(
        username=cfg.PRIVATE["database"]["site"]["user"],
        password=cfg.PRIVATE["database"]["site"]["pass"],
        host=cfg.PRIVATE["database"]["site"]["host"],
        port=cfg.PRIVATE["database"]["site"]["port"],
        db=cfg.PRIVATE["database"]["site"]["db"],
    ),
}

sqlalchemy_ext = SQLAlchemy(app)

api = Api(app)


from bapi.resources.bans import blp as bans_blueprint
from bapi.blueprints.discord import discord_blueprint
from bapi.resources.general import blp as general_blueprint
from bapi.resources.library import blp as library_blueprint
from bapi.resources.patreon import blp as patreon_blueprint
from bapi.resources.stats import blp as stats_blueprint

api.register_blueprint(bans_blueprint)
api.register_blueprint(general_blueprint)
api.register_blueprint(library_blueprint)
api.register_blueprint(patreon_blueprint)
api.register_blueprint(stats_blueprint)

# Register Discord blueprint
app.register_blueprint(discord_blueprint)


@app.route("/")
def docs_redirect():
    return redirect("/docs")
