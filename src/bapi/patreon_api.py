from typing import Any

import requests

API_BASE_URL = "https://www.patreon.com/api/oauth2/v2"
TOKEN_URL = "https://www.patreon.com/api/oauth2/token"
REQUEST_TIMEOUT_SECONDS = 10


class PatreonAPIError(RuntimeError):
    pass


def _request_json(method: str, url: str, **kwargs: Any) -> dict[str, Any]:
    try:
        response = requests.request(method, url, timeout=REQUEST_TIMEOUT_SECONDS, **kwargs)
        response.raise_for_status()
    except requests.RequestException as error:
        raise PatreonAPIError(f"Patreon request failed: {error}") from error

    try:
        payload = response.json()
    except requests.exceptions.JSONDecodeError as error:
        raise PatreonAPIError("Patreon returned an invalid JSON response") from error

    if not isinstance(payload, dict):
        raise PatreonAPIError("Patreon returned an unexpected response")

    if payload.get("errors"):
        raise PatreonAPIError("Patreon returned an API error")

    return payload


def exchange_oauth_code(client_id: str, client_secret: str, code: str, redirect_uri: str) -> str:
    payload = _request_json(
        "POST",
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
        },
        headers={"Accept": "application/json"},
    )
    access_token = payload.get("access_token")

    if not isinstance(access_token, str) or not access_token:
        raise PatreonAPIError("Patreon did not return an access token")

    return access_token


def get_identity_id(access_token: str) -> str:
    payload = _request_json(
        "GET",
        f"{API_BASE_URL}/identity",
        headers={"Accept": "application/json", "Authorization": f"Bearer {access_token}"},
    )
    identity = payload.get("data")

    if not isinstance(identity, dict):
        raise PatreonAPIError("Patreon identity response is missing its user resource")

    identity_id = identity.get("id")
    if not isinstance(identity_id, str) or not identity_id:
        raise PatreonAPIError("Patreon identity response is missing its user id")

    return identity_id


def get_campaign_income(access_token: str, campaign_id: str) -> int:
    url = f"{API_BASE_URL}/campaigns/{campaign_id}/members"
    headers = {"Accept": "application/json", "Authorization": f"Bearer {access_token}"}
    cursor: str | None = None
    seen_cursors: set[str] = set()
    income = 0

    while True:
        params = {
            "page[count]": 1000,
            "fields[member]": "currently_entitled_amount_cents",
        }
        if cursor is not None:
            params["page[cursor]"] = cursor

        payload = _request_json("GET", url, headers=headers, params=params)
        members = payload.get("data")
        if not isinstance(members, list):
            raise PatreonAPIError("Patreon campaign members response is missing its resources")

        for member in members:
            if not isinstance(member, dict):
                raise PatreonAPIError("Patreon campaign member response contains an invalid resource")

            attributes = member.get("attributes")
            if not isinstance(attributes, dict):
                raise PatreonAPIError("Patreon campaign member response is missing attributes")

            amount = attributes.get("currently_entitled_amount_cents")
            if isinstance(amount, bool) or not isinstance(amount, int) or amount < 0:
                raise PatreonAPIError("Patreon campaign member has an invalid pledge amount")

            income += amount

        cursor = _next_cursor(payload)
        if cursor is None:
            return income
        if cursor in seen_cursors:
            raise PatreonAPIError("Patreon campaign members pagination repeated a cursor")
        seen_cursors.add(cursor)


def _next_cursor(payload: dict[str, Any]) -> str | None:
    meta = payload.get("meta")
    if not isinstance(meta, dict):
        return None

    pagination = meta.get("pagination")
    if not isinstance(pagination, dict):
        return None

    cursors = pagination.get("cursors")
    if not isinstance(cursors, dict) or "next" not in cursors:
        return None

    cursor = cursors["next"]
    if cursor is None:
        return None
    if not isinstance(cursor, str) or not cursor:
        raise PatreonAPIError("Patreon campaign members response has an invalid pagination cursor")

    return cursor
