import math

from bapi import cfg
from bapi import db
from bapi.schemas import PaginationQuerySchema
from bapi.schemas import PaginationResultSchema
from flask import jsonify
from flask.views import MethodView
from flask_smorest import Blueprint


blp = Blueprint("library", "library", url_prefix="/library")


@blp.route("/")
class BookListResource(MethodView):
    @blp.doc(description="Get a paginated list of library books.")
    @blp.arguments(PaginationQuerySchema, location="query")
    @blp.response(200, PaginationResultSchema)
    def get(self, args):
        page = max(min(args.get("page") or 1, 1_000_000), 1)
        query = db.db_session.query(db.Book).filter(db.Book.deleted.is_(None)).order_by(db.Book.datetime.desc())
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


@blp.route("/<int:bookid>")
class BookResource(MethodView):
    @blp.doc(description="Get a single book from its `bookid`.")
    @blp.response(200, db.BookSchema)
    def get(self, bookid):
        book = db.Book.from_id(bookid)
        if not book:
            return jsonify({"error": "book not found"}), 404
        return book
