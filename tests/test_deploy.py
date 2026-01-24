"""Tests for deployment utilities."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from karabinerpyx import KarabinerConfig, Profile
from karabinerpyx.deploy import (
    backup_config,
    validate_json,
    validate_config,
    save_config,
    reload_karabiner,
)


class TestValidateJson:
    """Tests for validate_json function."""

    def test_valid_json(self):
        """Test valid JSON returns True."""
        assert validate_json('{"key": "value"}') is True

    def test_invalid_json(self):
        """Test invalid JSON returns False."""
        assert validate_json('{"key": invalid}') is False

    def test_empty_object(self):
        """Test empty object is valid."""
        assert validate_json("{}") is True

    def test_empty_string(self):
        """Test empty string is invalid."""
        assert validate_json("") is False


class TestValidateConfig:
    """Tests for validate_config function."""

    def test_valid_config(self):
        """Test valid config returns no errors."""
        config = {
            "global": {},
            "profiles": [{"name": "test"}],
        }
        errors = validate_config(config)
        assert errors == []

    def test_missing_global(self):
        """Test missing global key."""
        config = {"profiles": []}
        errors = validate_config(config)
        assert "Missing 'global' key" in errors

    def test_missing_profiles(self):
        """Test missing profiles key."""
        config = {"global": {}}
        errors = validate_config(config)
        assert "Missing 'profiles' key" in errors

    def test_profiles_not_list(self):
        """Test profiles not a list."""
        config = {"global": {}, "profiles": "invalid"}
        errors = validate_config(config)
        assert "'profiles' must be a list" in errors

    def test_empty_profiles(self):
        """Test empty profiles list."""
        config = {"global": {}, "profiles": []}
        errors = validate_config(config)
        assert "At least one profile is required" in errors


class TestBackupConfig:
    """Tests for backup_config function."""

    def test_backup_existing_file(self):
        """Test backing up an existing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "karabiner.json"
            config_path.write_text('{"test": true}')

            backup_path = backup_config(config_path)

            assert backup_path is not None
            assert backup_path.exists()
            assert "backup" in backup_path.name
            assert json.loads(backup_path.read_text()) == {"test": True}

    def test_backup_nonexistent_file(self):
        """Test backing up a nonexistent file returns None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "nonexistent.json"

            backup_path = backup_config(config_path)

            assert backup_path is None


class TestSaveConfig:
    """Tests for save_config function."""

    def test_save_to_custom_path(self):
        """Test saving config to custom path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "custom.json"

            config = KarabinerConfig()
            config.add_profile(Profile("Test"))

            result_path = save_config(config, config_path, backup=False)

            assert result_path == config_path
            assert config_path.exists()

            saved_data = json.loads(config_path.read_text())
            assert "global" in saved_data
            assert len(saved_data["profiles"]) == 1

    def test_save_creates_backup(self):
        """Test that save creates backup when file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "karabiner.json"
            config_path.write_text('{"old": true}')

            config = KarabinerConfig()
            config.add_profile(Profile("Test"))

            save_config(config, config_path, backup=True)

            backup_dir = Path(tmpdir) / "automatic_backups"
            backups = list(backup_dir.glob("karabiner_backup_*.json"))
            assert len(backups) == 1

    def test_save_invalid_config_raises(self):
        """Test that saving invalid config raises ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test.json"

            # Empty config (no profiles)
            config = KarabinerConfig()

            with pytest.raises(ValueError, match="Invalid configuration"):
                save_config(config, config_path)

    def test_save_with_string_path(self):
        """Test saving with string path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = f"{tmpdir}/test.json"

            config = KarabinerConfig()
            config.add_profile(Profile("Test"))

            result_path = save_config(config, config_path, backup=False)

            assert result_path == Path(config_path)

    def test_save_dry_run_no_write(self):
        """Test that dry_run does not write to disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test.json"

            config = KarabinerConfig()
            config.add_profile(Profile("Test"))

            result_path = save_config(config, config_path, dry_run=True)

            assert result_path == config_path
            assert not config_path.exists()

    def test_save_dry_run_diff(self, capsys):
        """Test that dry_run shows diff when file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test.json"
            config_path.write_text('{\n  "old": true\n}')

            config = KarabinerConfig()
            config.add_profile(Profile("Test"))

            save_config(config, config_path, dry_run=True)

            captured = capsys.readouterr()
            assert "Changes for" in captured.out
            # Check for diff symbols
            assert "-" in captured.out
            assert "+" in captured.out
            assert not config_path.read_text().strip() == config.build()


class TestReloadKarabiner:
    """Tests for reload_karabiner function."""

    @patch("karabinerpyx.deploy.subprocess.run")
    def test_reload_success_first_try(self, mock_run):
        """Test successful reload on first try."""
        mock_run.return_value = MagicMock(returncode=0)

        result = reload_karabiner()
        assert result is True

    @patch("karabinerpyx.deploy.subprocess.check_output")
    @patch("karabinerpyx.deploy.subprocess.run")
    def test_reload_success_second_try(self, mock_run, mock_check_output):
        """Test successful reload on second try (fallback)."""
        from subprocess import CalledProcessError

        # First call fails, second succeeds
        mock_run.side_effect = [
            CalledProcessError(1, "cmd"),
            MagicMock(returncode=0),
        ]
        mock_check_output.return_value = b"501"

        result = reload_karabiner()
        assert result is True

    @patch("karabinerpyx.deploy.subprocess.check_output")
    @patch("karabinerpyx.deploy.subprocess.run")
    def test_reload_failure(self, mock_run, mock_check_output):
        """Test reload failure."""
        from subprocess import CalledProcessError

        mock_run.side_effect = CalledProcessError(1, "cmd")
        mock_check_output.side_effect = CalledProcessError(1, "cmd")

        result = reload_karabiner()
        assert result is False
