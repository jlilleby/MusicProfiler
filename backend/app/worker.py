import asyncio
import logging
import random
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

from .config import settings
from .spotify import get_spotify
from .storage import status_update

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("musicprofiler.worker")


def retry_delay(header: str | None) -> float:
    if not header:
        return 60.0
    try:
        return max(1.0, min(3600.0, float(header)))
    except ValueError:
        try:
            dt = parsedate_to_datetime(header)
            return max(1.0, min(3600.0, (dt - datetime.now(timezone.utc)).total_seconds()))
        except (TypeError, ValueError):
            return 60.0


async def job(name: str, path: str, interval: int, params=None):
    # Bounded exponential backoff for transient failures; never spin on errors.
    consecutive_failures = 0
    while True:
        if not settings().collector_enabled:
            await asyncio.sleep(60)
            continue
        delay = max(15, interval)
        try:
            response = await get_spotify(path, params=params)
            if response is None:
                status_update(name, None, "not connected")
                delay = 60
            elif response.status_code in (200, 204):
                consecutive_failures = 0
                # Deliberately do NOT store raw playback or listening-history records.
                status_update(name, response.status_code, "ok", success=True)
                log.info("%s successful (%s)", name, response.status_code)
            elif response.status_code == 429:
                body = {}
                try:
                    body = response.json()
                except ValueError:
                    pass
                error = body.get("error", {}) if isinstance(body, dict) else {}
                reason = error.get("reason", "") if isinstance(error, dict) else ""
                if reason == "QUOTA_EXCEEDED":
                    delay = 3600
                    message = "quota exceeded; polling suspended for one hour"
                else:
                    delay = retry_delay(response.headers.get("Retry-After"))
                    message = "rate limited"
                until = datetime.now(timezone.utc) + timedelta(seconds=delay)
                status_update(name, 429, message, paused_until=until)
            elif response.status_code in (401, 403):
                status_update(name, response.status_code, "authentication or permission failure")
                delay = 3600
            else:
                consecutive_failures += 1
                delay = min(3600, max(interval, 2 ** min(consecutive_failures, 8) + random.random() * 5))
                status_update(name, response.status_code, "Spotify request failed")
        except Exception as exc:
            consecutive_failures += 1
            delay = min(3600, max(interval, 2 ** min(consecutive_failures, 8) + random.random() * 5))
            log.warning("%s error: %s", name, type(exc).__name__)
            try:
                status_update(name, None, f"connection failure: {type(exc).__name__}")
            except Exception:
                pass
        await asyncio.sleep(delay)


async def main():
    await asyncio.gather(
        job("recently_played", "/me/player/recently-played", settings().recent_poll_seconds, {"limit": 50}),
        job("current_playback", "/me/player", settings().playback_poll_seconds),
    )


if __name__ == "__main__":
    asyncio.run(main())
