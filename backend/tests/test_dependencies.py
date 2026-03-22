from dependencies import (
    record_login_attempt, is_ip_locked,
    blacklist_token, is_blacklisted,
    _login_attempts
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
