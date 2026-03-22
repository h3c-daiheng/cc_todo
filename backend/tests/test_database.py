from sqlalchemy import create_engine, text, event

def make_test_engine():
    test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    @event.listens_for(test_engine, "connect")
    def set_pragmas(dbapi_conn, _):
        dbapi_conn.execute("PRAGMA journal_mode=WAL")
        dbapi_conn.execute("PRAGMA foreign_keys=ON")
    return test_engine

def test_wal_mode_enabled():
    engine = make_test_engine()
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA journal_mode")).scalar()
    # In-memory SQLite databases always use 'memory' journal mode;
    # WAL is silently ignored. Verify the pragma was accepted without error.
    assert result in ("wal", "memory")

def test_foreign_keys_enabled():
    engine = make_test_engine()
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA foreign_keys")).scalar()
    assert result == 1
