from sqlalchemy import text
from database import engine

def test_wal_mode_enabled():
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA journal_mode")).scalar()
    assert result == "wal"

def test_foreign_keys_enabled():
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA foreign_keys")).scalar()
    assert result == 1
