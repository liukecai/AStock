from app.pg_dsn import DEFAULT_PG_DSN, resolve_pg_dsn


def test_resolve_pg_dsn_defaults_to_compose_service_host():
    assert resolve_pg_dsn(None) == DEFAULT_PG_DSN


def test_resolve_pg_dsn_preserves_explicit_host():
    dsn = "postgresql://aquant:changeme@db.internal:5432/aquant"
    assert resolve_pg_dsn(dsn) == dsn
