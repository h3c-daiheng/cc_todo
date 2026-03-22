from fastapi import HTTPException

from dependencies import (
    record_login_attempt, is_ip_locked,
    blacklist_token, is_blacklisted,
    _login_attempts,
    get_current_user,
)


def test_ip_not_locked_initially():
    assert not is_ip_locked("1.2.3.4")


def test_ip_locked_after_10_failures():
    ip = "10.0.0.99"
    _login_attempts.pop(ip, None)
    for _ in range(10):
        record_login_attempt(ip, False)
    assert is_ip_locked(ip)


def test_ip_not_locked_after_successes():
    ip = "10.0.0.88"
    _login_attempts.pop(ip, None)
    for _ in range(5):
        record_login_attempt(ip, True)
    assert not is_ip_locked(ip)


def test_blacklist_token():
    token = "some.jwt.token"
    assert not is_blacklisted(token)
    blacklist_token(token)
    assert is_blacklisted(token)


def test_get_current_user_rejects_non_numeric_sub(monkeypatch):
    monkeypatch.setattr("dependencies.decode_token", lambda token: {"sub": "abc"})

    class FakeDB:
        def get(self, model, user_id):
            return None

    try:
        get_current_user(credentials=type("Creds", (), {"credentials": "token"})(), db=FakeDB())
        assert False, "expected HTTPException"
    except HTTPException as exc:
        assert exc.status_code == 401
        assert exc.detail == "Token 无效或已过期"
