from __future__ import annotations

import json
import time
from pathlib import Path
import tempfile
from karabinerpyx.deploy import (
    backup_config,
    cleanup_backups,
    migrate_legacy_backups,
    list_backups,
    restore_config,
)


def test_cleanup_backups():
    with tempfile.TemporaryDirectory() as tmpdir:
        backup_dir = Path(tmpdir) / "automatic_backups"
        backup_dir.mkdir()

        # Create 15 backups
        for i in range(15):
            backup_path = backup_dir / f"karabiner_backup_20260124_{i:06d}.json"
            backup_path.write_text("{}")
            # Ensure different modification times
            atime = time.time() + i
            mtime = time.time() + i
            import os

            os.utime(backup_path, (atime, mtime))

        assert len(list(backup_dir.glob("karabiner_backup_*.json"))) == 15

        cleanup_backups(backup_dir, keep=10)

        remaining = sorted(list(backup_dir.glob("karabiner_backup_*.json")))
        assert len(remaining) == 10
        # Should keep the ones with largest i (latest mtime)
        assert "000014" in remaining[-1].name
        assert "000005" in remaining[0].name


def test_migrate_legacy_backups():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        config_path = tmp_path / "karabiner.json"
        config_path.write_text("{}")

        # Create legacy backups in the same dir
        legacy1 = tmp_path / "karabiner_backup_20250101_000000.json"
        legacy1.write_text('{"legacy": 1}')
        legacy2 = tmp_path / "karabiner_backup_20250101_111111.json"
        legacy2.write_text('{"legacy": 2}')

        backup_dir = tmp_path / "automatic_backups"
        backup_dir.mkdir()

        migrate_legacy_backups(config_path, backup_dir)

        assert not legacy1.exists()
        assert not legacy2.exists()
        assert (backup_dir / legacy1.name).exists()
        assert (backup_dir / legacy2.name).exists()


def test_backup_config_triggers_all():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        config_path = tmp_path / "karabiner.json"
        config_path.write_text('{"current": True}')

        # 1. Legacy backup exists
        legacy = tmp_path / "karabiner_backup_old.json"
        legacy.write_text("{}")

        # 2. Run backup_config
        backup_path = backup_config(config_path)

        backup_dir = tmp_path / "automatic_backups"
        assert backup_dir.exists()
        assert not legacy.exists()
        assert (backup_dir / legacy.name).exists()
        assert backup_path.exists()
        assert backup_path.parent == backup_dir


def test_list_and_restore_config():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        config_path = tmp_path / "karabiner.json"
        config_path.write_text('{"current": true}')

        backup_dir = tmp_path / "automatic_backups"
        backup_dir.mkdir()

        # Create a backup
        backup_path = backup_dir / "karabiner_backup_20260124_120000.json"
        backup_path.write_text('{"backup": true}')

        # 1. List backups
        backups = list_backups(config_path)
        assert len(backups) == 1
        assert backups[0] == backup_path

        # 2. Restore backup
        success = restore_config(backup_path, config_path)
        assert success is True
        assert json.loads(config_path.read_text()) == {"backup": True}
