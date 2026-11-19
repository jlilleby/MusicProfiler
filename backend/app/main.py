import secrets
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

from .config import settings
from .spotify import authorization_url, exchange_code, new_pkce
from .storage import connection

app = FastAPI(title="MusicProfiler API", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/status")
def status():
    with connection() as db:
        connected = db.execute(
            "SELECT EXISTS(SELECT 1 FROM spotify_auth WHERE account_key='primary') AS connected"
        ).fetchone()["connected"]
        jobs = db.execute(
            """SELECT job_name, last_success_at, last_attempt_at,
                      last_http_status, last_message, paused_until
               FROM collector_status ORDER BY job_name"""
        ).fetchall()
    return {
        "connected": connected,
        "recent_poll_seconds": settings().recent_poll_seconds,
        "playback_poll_seconds": settings().playback_poll_seconds,
        "collector_enabled": settings().collector_enabled,
        "jobs": jobs,
    }


@app.get("/auth/login")
def login():
    if not settings().spotify_client_id:
        raise HTTPException(503, "Configure SPOTIFY_CLIENT_ID first")
    state = secrets.token_urlsafe(32)
    verifier, challenge = new_pkce()
    with connection() as db:
        db.execute("DELETE FROM oauth_attempts WHERE expires_at < NOW()")
        db.execute(
            "INSERT INTO oauth_attempts(state,code_verifier,expires_at) VALUES (%s,%s,%s)",
            (state, verifier, datetime.now(timezone.utc) + timedelta(minutes=10)),
        )
    return RedirectResponse(authorization_url(state, challenge), status_code=302)


@app.get("/auth/callback")
async def callback(state: str = "", code: str = "", error: str = ""):
    if error:
        raise HTTPException(400, "Spotify authorization declined")
    if not code or not state:
        raise HTTPException(400, "Missing OAuth response parameters")
    with connection() as db:
        row = db.execute(
            "DELETE FROM oauth_attempts WHERE state=%s AND expires_at>NOW() RETURNING code_verifier",
            (state,),
        ).fetchone()
    if not row:
        raise HTTPException(400, "Invalid or expired OAuth state")
    try:
        await exchange_code(code, row["code_verifier"])
    except Exception:
        raise HTTPException(502, "Spotify token exchange failed")
    return HTMLResponse("<h1>Spotify connected</h1><p>You can close this page.</p>")


@app.post("/auth/disconnect")
def disconnect():
    # Local-only MVP: DO NOT expose publicly without authentication.
    with connection() as db:
        db.execute("DELETE FROM spotify_auth WHERE account_key='primary'")
    return {"disconnected": True}
