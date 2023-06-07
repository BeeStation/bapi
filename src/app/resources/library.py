import math

from flask import abort, jsonify, request
from flask_apispec import MethodResource, use_kwargs, marshal_with, doc
from flask_restful import Resource
from marshmallow import schema, fields

from app import cfg, db


class BookListResource(Resource):
    @doc(description="Get a paginated list of library books.")
    @use_kwargs(PaginationQuerySchema)
    @marshal_with(PaginationResultSchema)
    def get(self):
        page = max(min(kwargs.get("page", type=int, default=1), 1_000_000))
        query = db.db_session.query(db.Book).filter(db.Book.deleted == None).order_by(db.Book.datetime.desc())
        length = query.count()
        displayed_books = query.offset((page - 1) * cfg.API["items-per-page"]).limit(cfg.API["items-per-page"])

        return jsonify(
            {
                "page": page,
                "pages": math.ceil(length / cfg.API["items-per-page"]),
                "page_length": cfg.API["items-per-page"],
                "total_length": length,
                "data": [book.to_public_dict() for book in displayed_books],
            }
        )


class BookResource(Resource):
    @doc(description="Get a single book from its `bookid`.")
    @marshal_with(BookSchema)
    def get(self, bookid):
        book = db.Book.from_id(bookid)
        if not book: abort(404)
        return book
