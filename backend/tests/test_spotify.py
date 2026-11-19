from app.spotify import authorization_url, new_pkce
from app.worker import retry_delay


def test_pkce_is_url_safe_and_unique():
    a, challenge_a = new_pkce()
    b, challenge_b = new_pkce()
    assert a != b
    assert challenge_a != challenge_b
    assert "=" not in challenge_a


def test_authorization_url_contains_pkce(monkeypatch):
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "test-client")
    from app.config import settings
    settings.cache_clear()
    url = authorization_url("my-state", "my-challenge")
    assert "code_challenge_method=S256" in url
    assert "state=my-state" in url
    assert "client_id=test-client" in url
    settings.cache_clear()


def test_retry_delay():
    assert retry_delay("120") == 120
    assert retry_delay(None) == 60
    assert retry_delay("0") == 1
    assert retry_delay("99999") == 3600
