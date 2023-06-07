from os import environ

from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin

from flask import Flask, abort, redirect
from flask_cors import CORS
from flask_restful import Api
from flask_apispec import FlaskApiSpec
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from flask_swagger_ui import get_swaggerui_blueprint

from webargs.flaskparser import parser

parser.location = "query"

from app import cfg

app = Flask(__name__)

if environ.get("DEBUG") == "True":
    from werkzeug.debug import DebuggedApplication

    app.wsgi_app = DebuggedApplication(app.wsgi_app, True)

    app.debug = True

if environ.get("APM") == "True":
    from elasticapm.contrib.flask import ElasticAPM

    apm_url = "http://0.0.0.0:8200"
    apm_debug = False
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
        "DEBUG": apm_debug,
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


from app.resources.bans import BanListResource

api.add_resource(BanListResource, "/bans")
docs_ext.register(BanListResource)

from app.resources.general import (
    PlayerListResource,
    ServerListResource,
    ServerPlayerListResource,
    VersionResource,
)

api.add_resource(VersionResource, "/version")
api.add_resource(PlayerListResource, "/playerlist")
api.add_resource(ServerPlayerListResource, "/playerlist/<string:id>")
api.add_resource(ServerListResource, "/servers")
docs_ext.register(VersionResource)
docs_ext.register(PlayerListResource)
docs_ext.register(ServerPlayerListResource)
docs_ext.register(ServerListResource)

from app.resources.library import BookListResource, BookResource

api.add_resource(BookListResource, "/library")
api.add_resource(BookResource, "/library/<int:bookid>")
docs_ext.register(BookListResource)
docs_ext.register(BookResource)

from app.resources.patreon import (
    BudgetResource,
    LinkedPatreonListResource,
    PatreonOuathResource,
)

api.add_resource(PatreonOuathResource, "/patreonauth")
api.add_resource(LinkedPatreonListResource, "/linked_patreons")
api.add_resource(BudgetResource, "/budget")
docs_ext.register(PatreonOuathResource)
docs_ext.register(LinkedPatreonListResource)
docs_ext.register(BudgetResource)

from app.resources.stats import ServerStatsResource, StatsResource, StatsTotalsResource

api.add_resource(StatsResource, "/stats")
api.add_resource(ServerStatsResource, "/stats/<string:id>")
api.add_resource(StatsTotalsResource, "/stats/totals")
docs_ext.register(StatsResource)
docs_ext.register(ServerStatsResource)
docs_ext.register(StatsTotalsResource)

# Register the swagger docs blueprint
app.register_blueprint(get_swaggerui_blueprint("/docs", "/docs_json", config={"app_name": "BeeStation API"}))


@app.route("/")
def docs_redirect():
    return redirect("/docs")
