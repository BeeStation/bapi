import math

from flask import abort, jsonify, request

from flask_restful import Resource

from app import cfg, db


class BookListResource(Resource):
    def get(self):
        page = request.args.get("page", type=int, default=1)
        page = max(min(page, 1_000_000), 1)

        query = db.db_session.query(db.Book).order_by(db.Book.datetime.desc())

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
    def get(self, bookid):
        book = db.Book.from_id(bookid)

        if not book:
            return abort(404)

        return jsonify(book.to_public_dict())
