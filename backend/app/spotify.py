import asyncio
import base64
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx

from .config import settings
from .storage import connection, load_tokens, save_tokens

AUTHORIZE = "https://accounts.spotify.com/authorize"
TOKEN = "https://accounts.spotify.com/api/token"
API = "https://api.spotify.com/v1"
SCOPES = "user-read-recently-played user-read-playback-state"

# One process owns the worker's refresh lock. The API OAuth callback is independent.
_refresh_lock = asyncio.Lock()


def new_pkce() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).decode().rstrip("=")
    return verifier, challenge


def authorization_url(state: str, challenge: str) -> str:
    values = {
        "client_id": settings().spotify_client_id,
        "response_type": "code",
        "redirect_uri": settings().spotify_redirect_uri,
        "scope": SCOPES,
        "state": state,
        "code_challenge_method": "S256",
        "code_challenge": challenge,
    }
    return AUTHORIZE + "?" + urlencode(values)


async def token_exchange(values: dict) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(TOKEN, data=values)
        response.raise_for_status()
        return response.json()


async def exchange_code(code: str, verifier: str):
    payload = await token_exchange({
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings().spotify_redirect_uri,
        "client_id": settings().spotify_client_id,
        "code_verifier": verifier,
    })
    save_tokens(payload["access_token"], payload["refresh_token"], int(payload["expires_in"]))


async def access_token(force_refresh=False):
    async with _refresh_lock:
        current = load_tokens()
        if not current:
            return None
        if not force_refresh and current["expires_at"] > datetime.now(timezone.utc):
            return current["access"]
        payload = await token_exchange({
            "grant_type": "refresh_token",
            "refresh_token": current["refresh"],
            "client_id": settings().spotify_client_id,
        })
        save_tokens(
            payload["access_token"],
            payload.get("refresh_token", current["refresh"]),
            int(payload["expires_in"]),
        )
        return payload["access_token"]


async def get_spotify(path: str, params=None):
    token = await access_token()
    if token is None:
        return None
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(
            API + path,
            params=params,
            headers={"Authorization": f"Bearer {token}"},
        )
        if response.status_code == 401:
            token = await access_token(force_refresh=True)
            response = await client.get(
                API + path, params=params,
                headers={"Authorization": f"Bearer {token}"},
            )
        return response
