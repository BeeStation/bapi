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


class PatreonLinkSchema(Schema):
    ckey = fields.String()
    patreon_id = fields.String()


class BudgetSchema(Schema):
    income = fields.Integer()
    goal = fields.Integer()
    percent = fields.Integer()


class StatsTotalsSchema(Schema):
    total_players = fields.Integer()
    total_rounds = fields.Integer()
    total_connections = fields.Integer()
