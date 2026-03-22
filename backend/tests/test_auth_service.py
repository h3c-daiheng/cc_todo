from services.auth import hash_password, verify_password, create_access_token, decode_token

def test_password_hash_and_verify():
    pwd = "MySecret123"
    hashed = hash_password(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed)
    assert not verify_password("wrong", hashed)

def test_access_token_roundtrip():
    token = create_access_token({"sub": "42"})
    payload = decode_token(token)
    assert payload["sub"] == "42"

def test_expired_token_returns_none():
    from services.auth import create_token_with_expiry
    from datetime import timedelta
    token = create_token_with_expiry({"sub": "1"}, timedelta(seconds=-1))
    payload = decode_token(token)
    assert payload is None
