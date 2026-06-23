from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
import sys

from ..config import settings


def backup_db() -> str:
    """Perform atomic online backup of the active SQLite database and keep last 7 files."""
    if settings.database_url:
        print("[BACKUP INFO] Using PostgreSQL backend; skipping local SQLite backup.")
        return ""

    try:
        backup_dir = settings.data_dir / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"aquant_backup_{timestamp}.db"

        # Perform atomic online backup to protect against active writes
        with sqlite3.connect(settings.database_path) as source:
            with sqlite3.connect(backup_file) as target:
                source.backup(target)

        print(f"[BACKUP SUCCESS] Database backup created at: {backup_file}")

        # Rotate backups to keep only the last 7 items based on file modification time
        all_backups = sorted(
            backup_dir.glob("aquant_backup_*.db"),
            key=lambda p: p.stat().st_mtime
        )
        if len(all_backups) > 7:
            for old_backup in all_backups[:-7]:
                try:
                    old_backup.unlink()
                    print(f"[BACKUP ROTATION] Deleted old backup: {old_backup}")
                except OSError as e:
                    print(f"[BACKUP WARNING] Failed to delete old backup {old_backup}: {e}", file=sys.stderr)

        return str(backup_file)

    except Exception as e:
        print(f"[BACKUP ERROR] Failed to perform database backup: {e}", file=sys.stderr)
        raise
