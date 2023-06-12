from marshmallow import fields
from marshmallow import Schema


class PaginationSearchQuerySchema(Schema):
    page = fields.Integer(required=False)
    search_query = fields.String(required=False)


class PaginationQuerySchema(Schema):
    page = fields.Integer(required=False)


class PaginationResultSchema(Schema):
    page = fields.Integer()
    pages = fields.Integer()
    pange_length = fields.Integer()
    total_length = fields.Integer()
    data = fields.List(fields.Dict())


class APIPasswordRequiredSchema(Schema):
    api_pass = fields.String(required=True, data_key="pass")
