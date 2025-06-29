import math

from bapi import cfg
from bapi import db
from bapi.schemas import PaginationResultSchema
from bapi.schemas import PaginationSearchQuerySchema
from flask.views import MethodView
from flask_smorest import Blueprint


blp = Blueprint("bans", "bans", url_prefix="/bans")


@blp.route("/")
class BanListResource(MethodView):
    @blp.doc(description="Get a paginated list of bans.")
    @blp.arguments(PaginationSearchQuerySchema, location="query")
    @blp.response(200, PaginationResultSchema)
    def get(self, args):
        page = max(min(args.get("page") or 1, 1_000_000), 1)
        query = db.query_grouped_bans(search_query=args.get("search_query"))
        length = query.count()

        displayed_bans = query.offset((page - 1) * cfg.API["items-per-page"]).limit(cfg.API["items-per-page"])

        return {
            "page": page,
            "pages": math.ceil(length / cfg.API["items-per-page"]),
            "page_length": cfg.API["items-per-page"],
            "total_length": length,
            "data": [db.Ban.to_public_dict(ban) for ban in displayed_bans],
        }
