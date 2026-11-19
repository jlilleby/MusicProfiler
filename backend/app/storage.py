from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

import psycopg
from cryptography.fernet import Fernet
from psycopg.rows import dict_row

from .config import settings


@contextmanager
def connection():
    with psycopg.connect(settings().database_url, row_factory=dict_row) as conn:
        yield conn


def cipher() -> Fernet:
    key = settings().token_encryption_key
    if not key:
        raise RuntimeError("TOKEN_ENCRYPTION_KEY is required")
    return Fernet(key.encode())


def save_tokens(access: str, refresh: str, expires_in: int):
    expires = datetime.now(timezone.utc) + timedelta(seconds=max(0, expires_in - 60))
    with connection() as db:
        db.execute(
            """INSERT INTO spotify_auth(account_key, access_token_encrypted, refresh_token_encrypted, expires_at)
               VALUES ('primary', %s, %s, %s)
               ON CONFLICT (account_key) DO UPDATE SET
               access_token_encrypted=EXCLUDED.access_token_encrypted,
               refresh_token_encrypted=EXCLUDED.refresh_token_encrypted,
               expires_at=EXCLUDED.expires_at""",
            (cipher().encrypt(access.encode()).decode(), cipher().encrypt(refresh.encode()).decode(), expires),
        )


def load_tokens():
    with connection() as db:
        row = db.execute("SELECT * FROM spotify_auth WHERE account_key='primary'").fetchone()
    if not row:
        return None
    return {
        "access": cipher().decrypt(row["access_token_encrypted"].encode()).decode(),
        "refresh": cipher().decrypt(row["refresh_token_encrypted"].encode()).decode(),
        "expires_at": row["expires_at"],
    }


def status_update(name: str, code: int | None, message: str, success=False, paused_until=None):
    with connection() as db:
        db.execute(
            """INSERT INTO collector_status
                 (job_name,last_attempt_at,last_success_at,last_http_status,last_message,paused_until)
               VALUES (%s,NOW(),CASE WHEN %s THEN NOW() ELSE NULL END,%s,%s,%s)
               ON CONFLICT(job_name) DO UPDATE SET
                 last_attempt_at=NOW(),
                 last_success_at=CASE WHEN %s THEN NOW() ELSE collector_status.last_success_at END,
                 last_http_status=EXCLUDED.last_http_status,
                 last_message=EXCLUDED.last_message,
                 paused_until=EXCLUDED.paused_until""",
            (name, success, code, message[:200], paused_until, success),
        )
