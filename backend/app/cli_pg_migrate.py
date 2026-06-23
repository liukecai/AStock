"""
cli_pg_migrate.py
-----------------
One-shot SQLite → PostgreSQL data migration script.

Usage:
    PYTHONPATH=. python -m app.cli_pg_migrate \
        --sqlite /app/data/aquant.db \
        --pg "postgresql://aquant:changeme@localhost:5432/aquant"

Steps:
1. Read all rows from the SQLite database in foreign-key-safe order.
2. Initialise the PostgreSQL schema (via init_db() with DATABASE_URL set).
3. Batch-insert each table, skipping rows that already exist (ON CONFLICT DO NOTHING).
4. Print row-count comparison between SQLite and PostgreSQL for verification.

Run this ONCE on a cold PostgreSQL database. Safe to re-run (idempotent inserts).
"""
from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from typing import Any


def _pg_connect(dsn: str):
    try:
        import psycopg2
        import psycopg2.extras
        conn = psycopg2.connect(dsn, cursor_factory=psycopg2.extras.RealDictCursor)
        conn.autocommit = False
        return conn
    except ImportError:
        print("ERROR: psycopg2 is not installed. Run: pip install psycopg2-binary", file=sys.stderr)
        sys.exit(1)


def _sqlite_read(path: str, table: str) -> list[dict[str, Any]]:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(f"SELECT * FROM {table}")
        return [dict(r) for r in cur.fetchall()]
    except sqlite3.OperationalError:
        return []
    finally:
        conn.close()


def _pg_insert_batch(pg_conn, table: str, rows: list[dict[str, Any]]) -> int:
    if not rows:
        return 0
    import psycopg2.extras
    cols = list(rows[0].keys())
    cols_sql = ", ".join(cols)
    vals_sql = ", ".join(["%s"] * len(cols))
    sql = (
        f"INSERT INTO {table} ({cols_sql}) VALUES ({vals_sql}) "
        "ON CONFLICT DO NOTHING"
    )
    values = [tuple(row[c] for c in cols) for row in rows]
    cur = pg_conn.cursor()
    cur.executemany(sql, values)
    return cur.rowcount


# Ordered to respect foreign key constraints
TABLES = [
    "stocks",
    "daily_prices",
    "signals",
    "jobs",
    "news_items",
    "news_stock_links",
    "commodity_sector_mappings",
    "sector_stock_exposures",
    "company_commodity_profiles",
    "events",
    "commodity_impacts",
    "event_stock_scores",
    "event_earnings_impacts",
    "event_stock_reaction_scores_v2",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate SQLite → PostgreSQL for A-Quant")
    parser.add_argument("--sqlite", required=True, help="Path to SQLite .db file")
    parser.add_argument("--pg", required=True, help="PostgreSQL DSN (postgresql://...)")
    args = parser.parse_args()

    print(f"=== A-Quant SQLite → PostgreSQL Migration ===")
    print(f"  SQLite: {args.sqlite}")
    print(f"  PG DSN: {args.pg[:40]}...")
    print()

    # Initialise PG schema
    os.environ["DATABASE_URL"] = args.pg
    # Reload settings singleton (it's frozen; recreate module-level object)
    import importlib
    import app.config as cfg_mod
    import dataclasses
    object.__setattr__(cfg_mod.settings, "database_url", args.pg)

    from app.db import init_db
    print("[1/3] Initialising PostgreSQL schema...")
    init_db()
    print("  Schema ready.")

    pg_conn = _pg_connect(args.pg)

    try:
        print("\n[2/3] Migrating data...")
        results = {}
        for table in TABLES:
            rows = _sqlite_read(args.sqlite, table)
            if not rows:
                results[table] = (0, 0)
                continue
            inserted = _pg_insert_batch(pg_conn, table, rows)
            results[table] = (len(rows), inserted)
            print(f"  {table:45s} {len(rows):6d} rows read, {inserted:6d} inserted")

        pg_conn.commit()
        print("\n[3/3] Verifying row counts...")

        # Double-check counts in PG
        cur = pg_conn.cursor()
        for table in TABLES:
            cur.execute(f"SELECT COUNT(*) AS n FROM {table}")
            pg_count = cur.fetchone()["n"]
            src_count = results[table][0]
            status = "✅" if pg_count >= src_count else "⚠️ "
            print(f"  {status} {table:43s} SQLite={src_count:6d}  PG={pg_count:6d}")

        print("\nMigration complete.")
    except Exception as e:
        pg_conn.rollback()
        print(f"\nERROR during migration: {e}", file=sys.stderr)
        raise
    finally:
        pg_conn.close()


if __name__ == "__main__":
    main()
