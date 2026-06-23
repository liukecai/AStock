from __future__ import annotations

import os
from pathlib import Path

from app import db
from app.config import settings
from app.services.backup import backup_db


def test_database_backup_and_rotation(tmp_path):
    original_url = settings.database_url
    original_path = settings.database_path
    original_data_dir = settings.data_dir

    # Modify settings in place
    object.__setattr__(settings, "database_url", None)
    object.__setattr__(settings, "database_path", tmp_path / "aquant.db")
    object.__setattr__(settings, "data_dir", tmp_path)

    try:
        db.init_db()

        # Perform a single backup
        backup_file = backup_db()
        assert os.path.exists(backup_file)
        assert Path(backup_file).name.startswith("aquant_backup_")

        # Perform multiple backups to trigger rotation (we need at least 8 to prune down to 7)
        backup_dir = tmp_path / "backups"

        # Create 10 mock backup files with old timestamps/mtimes to test rotation
        for i in range(10):
            mock_file = backup_dir / f"aquant_backup_mock_{i}.db"
            mock_file.write_text("dummy database content")
            # Change file modification time so they sort chronologically
            os.utime(mock_file, (1700000000 + i, 1700000000 + i))

        # Run the backup job once more, which will check the files and prune
        backup_db()

        # The backups directory should contain exactly 7 files now (pruned down from 10 + new backup)
        current_backups = list(backup_dir.glob("aquant_backup_*.db"))
        assert len(current_backups) == 7

    finally:
        object.__setattr__(settings, "database_url", original_url)
        object.__setattr__(settings, "database_path", original_path)
        object.__setattr__(settings, "data_dir", original_data_dir)
