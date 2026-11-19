# MusicProfiler

Self-hosted starter for a Spotify Web API integration. Includes a FastAPI service, an OAuth 2.0 Authorization Code + PKCE flow, a PostgreSQL database, a worker with configurable schedules, and a minimal Next.js status dashboard.

> **Important:** Spotify's developer terms restrict certain derived listening metrics, profiling and AI uses of Spotify Platform data. This starter shows current playback and collector health and uses only minimal, short-lived playback data. Long-term API-derived listening analytics and skip inference are **not implemented**. The existing personal Spotify data export can be imported into a separate historical module in a future change, subject to applicable requirements.

## Quick start

1. Install Docker Compose.
2. Create an application in [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).
3. Add the redirect URI `http://127.0.0.1:8000/auth/callback` to its allowed redirect URIs. If Spotify rejects an HTTP redirect URI, use a valid HTTPS callback and set `SPOTIFY_REDIRECT_URI` and your reverse-proxy settings accordingly.
4. Copy `.env.example` to `.env`. Set `SPOTIFY_CLIENT_ID`, `DATABASE_PASSWORD` and `TOKEN_ENCRYPTION_KEY`. Generate the key with:
   ```bash
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```
5. Run `docker compose up --build -d`.
6. Open `http://127.0.0.1:8000/auth/login` on the machine hosting Docker and authorize Spotify.
7. Open `http://127.0.0.1:3000` for the status page.

For access from another computer, use a HTTPS reverse proxy / private VPN, and change the registered redirect URI accordingly. Do not expose the API unauthenticated to the internet.

## Services

- `api`: FastAPI, OAuth endpoints, health and collector status.
- `worker`: one scheduled collector; recent plays every 300 seconds, playback every 30 seconds by default.
- `db`: PostgreSQL 17, with initial schema created automatically.
- `web`: minimal Next.js status dashboard.

## Local commands

```bash
docker compose up --build
docker compose logs -f worker
docker compose down
```

Run backend tests outside Docker:

```bash
pip install -r backend/requirements.txt -r backend/requirements-dev.txt
PYTHONPATH=backend pytest backend/tests
```

## API behavior

- `GET /health` checks basic API process health.
- `GET /api/status` shows collector operational state (no tokens or raw listening history).
- `GET /auth/login` initiates OAuth with state and PKCE.
- `GET /auth/callback` exchanges the authorization code and encrypts tokens at rest.
- `POST /auth/disconnect` deletes the stored Spotify authorization; this endpoint is local-only and must not be exposed publicly without authentication.

The worker uses `GET /v1/me/player` and `GET /v1/me/player/recently-played?limit=50`. Recent history is inspected for successful fetches and status, but **not persisted as a listening-history profile** in this starter. The API does not expose definitive skip events. Spotify quotas can prevent the configured polling cadence.

## Security and policy

- No Spotify client secret is needed: the application uses OAuth + PKCE.
- Spotify tokens are encrypted with Fernet in PostgreSQL.
- Do not commit `.env`, tokens, exports or IP-address-bearing listening history.
- Ports bind to loopback by default; add authentication before remote exposure.
- Only one worker replica is supported; use a distributed lock before scaling.
- Inspect Spotify's [developer policy](https://developer.spotify.com/policy) before building persistent API-derived analytics or playlist ranking.

## Roadmap

1. Authentication and collection health (this starter).
2. Automated migrations, authenticated admin UI, HTTPS deployment.
3. Separate local import of personal streaming exports.
4. Authorized enrichment / recommendations only where Spotify terms permit.
