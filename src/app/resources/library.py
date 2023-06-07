import math

from flask import abort, jsonify, request
from flask_apispec import MethodResource, doc, marshal_with, use_kwargs
from flask_restful import Resource
from marshmallow import Schema, fields

from app import cfg, db, ma_ext
from app.schemas import *


class BookListResource(MethodResource):
    @doc(description="Get a paginated list of library books.")
    @use_kwargs(PaginationQuerySchema)
    @marshal_with(PaginationResultSchema)
    def get(self, **kwargs):
        page = max(min(kwargs.get("page") or 1, 1_000_000), 1)
        query = db.db_session.query(db.Book).filter(db.Book.deleted == None).order_by(db.Book.datetime.desc())
        length = query.count()
        displayed_books = query.offset((page - 1) * cfg.API["items-per-page"]).limit(cfg.API["items-per-page"])

        return jsonify(
            {
                "page": page,
                "pages": math.ceil(length / cfg.API["items-per-page"]),
                "page_length": cfg.API["items-per-page"],
                "total_length": length,
                "data": [db.BookSchema().dump(book) for book in displayed_books],
            }
        )


class BookResource(MethodResource):
    @doc(description="Get a single book from its `bookid`.")
    @marshal_with(db.BookSchema)
    def get(self, bookid):
        book = db.Book.from_id(bookid)
        if not book:
            abort(404, {"error": "book not found"})
        return book
