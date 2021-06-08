from app import cfg
from app import db
from app import util

from flask import Blueprint, abort, jsonify, request

import math

bp_library = Blueprint('library', __name__)

@bp_library.route("/library")
def page_library():
	page = request.args.get('page', type=int, default=1)
	page = max(min(page, 1_000_000), 1)

	query = db.db_session.query(db.Book).order_by(db.Book.datetime.desc())

	length = query.count()

	displayed_books = query.offset((page-1)*cfg.API["items-per-page"]).limit(page*cfg.API["items-per-page"])
	
	return jsonify({
		"page": page,
		"pages":  math.ceil(length / cfg.API["items-per-page"]),
		"page_length": cfg.API["items-per-page"],
		"total_length": length,

		"data": [
			 book.to_public_dict() for book in displayed_books
		]
	})


@bp_library.route("/library/<int:bookid>")
def page_library_book(bookid):
	book = db.Book.from_id(bookid)
	
	if not book:
		return abort(404)
	
	return jsonify(book.to_public_dict())
