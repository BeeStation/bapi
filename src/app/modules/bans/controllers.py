from app import cfg
from app import db
from app import util

from flask import Blueprint, jsonify, render_template, request

import math

bp_bans = Blueprint('bans', __name__)

@bp_bans.route("/bans")
def page_bans():
	page = request.args.get('page', type=int, default=1)
	page = max(min(page, 1_000_000), 1) # Arbitrary number. We probably won't ever have to deal with 1,000,000 pages of bans. Hopefully..

	search_query = request.args.get('search_query', type=str, default="")

	query = db.query_grouped_bans(search_query=search_query)
	
	length = query.count()

	displayed_bans = query.offset((page-1)*cfg.API["items-per-page"]).limit(page*cfg.API["items-per-page"])

	return jsonify({
		"page": page,
		"pages": math.ceil(length / cfg.API["items-per-page"]),
		"page_length": cfg.API["items-per-page"],
		"total_length": length,

		"data": [
			 db.Ban.to_public_dict(ban) for ban in displayed_bans
		]
	})