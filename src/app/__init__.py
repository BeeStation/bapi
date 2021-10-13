from os import environ

from flask import Flask
from flask_cors import CORS
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy

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


@app.context_processor
def context_processor():
    from app import db, util

    return dict(cfg=cfg, db=db, util=util)


from app.resources.bans import BanListResource

api.add_resource(BanListResource, "/bans")

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

from app.resources.library import BookListResource, BookResource

api.add_resource(BookListResource, "/library")
api.add_resource(BookResource, "/library/<int:bookid>")

from app.resources.patreon import (
    BudgetResource,
    LinkedPatreonListResource,
    PatreonOuathResource,
)

api.add_resource(PatreonOuathResource, "/patreonauth")
api.add_resource(LinkedPatreonListResource, "/linked_patreons")
api.add_resource(BudgetResource, "/budget")

from app.resources.stats import ServerStatsResource, StatsResource, StatsTotalsResource

api.add_resource(StatsResource, "/stats")
api.add_resource(ServerStatsResource, "/stats/<string:id>")
api.add_resource(StatsTotalsResource, "/stats/totals")
