CREATE TABLE IF NOT EXISTS spotify_auth (
  account_key TEXT PRIMARY KEY DEFAULT 'primary',
  access_token_encrypted TEXT NOT NULL,
  refresh_token_encrypted TEXT NOT NULL,
  expires_at TIMESTAMPTZ NOT NULL,
  connected_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS oauth_attempts (
  state TEXT PRIMARY KEY,
  code_verifier TEXT NOT NULL,
  expires_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS collector_status (
  job_name TEXT PRIMARY KEY,
  last_success_at TIMESTAMPTZ,
  last_attempt_at TIMESTAMPTZ,
  last_http_status INTEGER,
  last_message TEXT,
  paused_until TIMESTAMPTZ
);
