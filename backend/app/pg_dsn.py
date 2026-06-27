from __future__ import annotations


DEFAULT_PG_DSN = "postgresql://aquant:changeme@postgres:5432/aquant"


def resolve_pg_dsn(db_url: str | None) -> str:
    return db_url or DEFAULT_PG_DSN
