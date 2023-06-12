import math

from bapi import cfg
from bapi import db
from bapi.schemas import PaginationResultSchema
from bapi.schemas import PaginationSearchQuerySchema
from flask_apispec import doc
from flask_apispec import marshal_with
from flask_apispec import MethodResource
from flask_apispec import use_kwargs


class BanListResource(MethodResource):
    @doc(description="Get a paginated list of bans.")
    @use_kwargs(PaginationSearchQuerySchema)
    @marshal_with(PaginationResultSchema)
    def get(self, **kwargs):
        page = max(min(kwargs.get("page") or 1, 1_000_000), 1)
        query = db.query_grouped_bans(search_query=kwargs.get("search_query"))
        length = query.count()

        displayed_bans = query.offset((page - 1) * cfg.API["items-per-page"]).limit(cfg.API["items-per-page"])

        return {
            "page": page,
            "pages": math.ceil(length / cfg.API["items-per-page"]),
            "page_length": cfg.API["items-per-page"],
            "total_length": length,
            "data": [db.Ban.to_public_dict(ban) for ban in displayed_bans],
        }
