"""Tests for deployment utilities."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from karabinerpyx import KarabinerConfig, Profile
from karabinerpyx.deploy import (
    SaveResult,
    backup_config,
    reload_karabiner,
    save_config,
    validate_config,
    validate_json,
)


class TestValidateJson:
    def test_valid_json(self):
        assert validate_json('{"key": "value"}') is True

    def test_invalid_json(self):
        assert validate_json('{"key": invalid}') is False

    def test_empty_object(self):
        assert validate_json("{}") is True

    def test_empty_string(self):
        assert validate_json("") is False


class TestValidateConfig:
    def test_valid_config(self):
        config = {"global": {}, "profiles": [{"name": "test"}]}
        errors = validate_config(config)
        assert errors == []

    def test_missing_global(self):
        config = {"profiles": []}
        errors = validate_config(config)
        assert "Missing 'global' key" in errors

    def test_missing_profiles(self):
        config = {"global": {}}
        errors = validate_config(config)
        assert "Missing 'profiles' key" in errors

    def test_profiles_not_list(self):
        config = {"global": {}, "profiles": "invalid"}
        errors = validate_config(config)
        assert "'profiles' must be a list" in errors

    def test_empty_profiles(self):
        config = {"global": {}, "profiles": []}
        errors = validate_config(config)
        assert "At least one profile is required" in errors


class TestBackupConfig:
    def test_backup_existing_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "karabiner.json"
            config_path.write_text('{"test": true}')

            backup_path = backup_config(config_path)

            assert backup_path is not None
            assert backup_path.exists()
            assert "backup" in backup_path.name
            assert json.loads(backup_path.read_text()) == {"test": True}

    def test_backup_nonexistent_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "nonexistent.json"
            backup_path = backup_config(config_path)
            assert backup_path is None


class TestSaveConfig:
    def test_save_to_custom_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "custom.json"

            config = KarabinerConfig().add_profile(Profile("Test"))
            result = save_config(config, config_path, backup=False)

            assert isinstance(result, SaveResult)
            assert result.path == config_path
            assert config_path.exists()

            saved_data = json.loads(config_path.read_text())
            assert "global" in saved_data
            assert len(saved_data["profiles"]) == 1

    def test_save_creates_backup(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "karabiner.json"
            config_path.write_text('{"old": true}')

            config = KarabinerConfig().add_profile(Profile("Test"))
            result = save_config(config, config_path, backup=True)

            assert result.backup_path is not None
            assert result.backup_path.exists()

    def test_save_invalid_config_raises(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test.json"
            config = KarabinerConfig()
            with pytest.raises(ValueError, match="Invalid configuration"):
                save_config(config, config_path)

    def test_save_with_string_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = f"{tmpdir}/test.json"
            config = KarabinerConfig().add_profile(Profile("Test"))
            result = save_config(config, config_path, backup=False)
            assert result.path == Path(config_path)

    def test_save_dry_run_no_write(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test.json"
            config = KarabinerConfig().add_profile(Profile("Test"))

            result = save_config(config, config_path, dry_run=True)

            assert result.path == config_path
            assert result.dry_run is True
            assert not config_path.exists()

    def test_save_dry_run_diff(self, capsys):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test.json"
            config_path.write_text('{\n  "old": true\n}')

            config = KarabinerConfig().add_profile(Profile("Test"))

            result = save_config(config, config_path, dry_run=True)

            captured = capsys.readouterr()
            assert "Changes for" in captured.out
            assert result.diff_changed is True


class TestReloadKarabiner:
    @patch("karabinerpyx.deploy.subprocess.run")
    def test_reload_success_first_try(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        assert reload_karabiner() is True

    @patch("karabinerpyx.deploy.subprocess.check_output")
    @patch("karabinerpyx.deploy.subprocess.run")
    def test_reload_success_second_try(self, mock_run, mock_check_output):
        from subprocess import CalledProcessError

        mock_run.side_effect = [CalledProcessError(1, "cmd"), MagicMock(returncode=0)]
        mock_check_output.return_value = "501"
        assert reload_karabiner() is True

    @patch("karabinerpyx.deploy.subprocess.check_output")
    @patch("karabinerpyx.deploy.subprocess.run")
    def test_reload_failure(self, mock_run, mock_check_output):
        from subprocess import CalledProcessError

        mock_run.side_effect = CalledProcessError(1, "cmd")
        mock_check_output.side_effect = CalledProcessError(1, "cmd")
        assert reload_karabiner() is False
