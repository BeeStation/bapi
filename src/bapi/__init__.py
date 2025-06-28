import secrets
from os import environ

from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from bapi import cfg
from flask import abort
from flask import Flask
from flask import redirect
from flask_apispec import FlaskApiSpec
from flask_cors import CORS
from flask_marshmallow import Marshmallow
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy
from flask_swagger_ui import get_swaggerui_blueprint
from webargs.flaskparser import parser

parser.location = "query"

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


app.config["APISPEC_SPEC"] = APISpec(
    title="BeeStation API",
    version="v2",
    openapi_version="2.0",
    plugins=[MarshmallowPlugin()],
)

app.config["APISPEC_SWAGGER_URL"] = "/docs_json"

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

ma_ext = Marshmallow(app)
docs_ext = FlaskApiSpec(app)


# This error handler is necessary for usage with Flask-RESTful
@parser.error_handler
def handle_request_parsing_error(err, req, schema, *, error_status_code, error_headers):
    abort(400, err.messages)


from bapi.resources.bans import BanListResource
from bapi.blueprints.discord import discord_blueprint
from bapi.resources.general import PlayerListResource
from bapi.resources.general import ServerListResource
from bapi.resources.general import ServerPlayerListResource
from bapi.resources.general import VersionResource
from bapi.resources.library import BookListResource
from bapi.resources.library import BookResource
from bapi.resources.patreon import BudgetResource
from bapi.resources.patreon import LinkedPatreonListResource
from bapi.resources.patreon import PatreonOAuthResource
from bapi.resources.stats import ServerStatsResource
from bapi.resources.stats import StatsResource
from bapi.resources.stats import StatsTotalsResource

api.add_resource(BanListResource, "/bans")
docs_ext.register(BanListResource)


api.add_resource(VersionResource, "/version")
api.add_resource(PlayerListResource, "/playerlist")
api.add_resource(ServerPlayerListResource, "/playerlist/<string:id>")
api.add_resource(ServerListResource, "/servers")
docs_ext.register(VersionResource)
docs_ext.register(PlayerListResource)
docs_ext.register(ServerPlayerListResource)
docs_ext.register(ServerListResource)


api.add_resource(BookListResource, "/library")
api.add_resource(BookResource, "/library/<int:bookid>")
docs_ext.register(BookListResource)
docs_ext.register(BookResource)


api.add_resource(PatreonOAuthResource, "/patreonauth")
api.add_resource(LinkedPatreonListResource, "/linked_patreons")
api.add_resource(BudgetResource, "/budget")
docs_ext.register(PatreonOAuthResource)
docs_ext.register(LinkedPatreonListResource)
docs_ext.register(BudgetResource)


api.add_resource(StatsResource, "/stats")
api.add_resource(ServerStatsResource, "/stats/<string:id>")
api.add_resource(StatsTotalsResource, "/stats/totals")
docs_ext.register(StatsResource)
docs_ext.register(ServerStatsResource)
docs_ext.register(StatsTotalsResource)

# Register the swagger docs blueprint
app.register_blueprint(get_swaggerui_blueprint("/docs", "/docs_json", config={"app_name": "BeeStation API"}))

# Register Discord blueprint
app.register_blueprint(discord_blueprint)


@app.route("/")
def docs_redirect():
    return redirect("/docs")
