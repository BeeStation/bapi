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


def get_campaign_income(campaign_id: str) -> int:
    payload = _request_json(
        "GET",
        f"https://www.patreon.com/api/campaigns/{campaign_id}",
        headers={"Accept": "application/json", "User-Agent": "Mozilla/5.0 (compatible; BeeStation-BAPI)"},
    )
    data = payload.get("data")
    if not isinstance(data, dict):
        raise PatreonAPIError("Patreon campaign response is missing its campaign resource")

    attributes = data.get("attributes")
    if not isinstance(attributes, dict):
        raise PatreonAPIError("Patreon campaign response is missing its attributes")

    pledge_sum = attributes.get("pledge_sum")
    if isinstance(pledge_sum, bool) or not isinstance(pledge_sum, int) or pledge_sum < 0:
        raise PatreonAPIError("Patreon campaign response has an invalid pledge sum")

    return pledge_sum
