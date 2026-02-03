"""Deployment utilities for Karabiner configuration."""

from __future__ import annotations

import difflib
import json
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from karabinerpyx.models import KarabinerConfig

# Default Karabiner config path
DEFAULT_CONFIG_PATH = Path.home() / ".config" / "karabiner" / "karabiner.json"

# Backup settings
MAX_BACKUPS = 10


def migrate_legacy_backups(config_path: Path, backup_dir: Path) -> None:
    """Migrate legacy backups from the config directory to the backup directory.

    Args:
        config_path: Path to the config file.
        backup_dir: Path to the backup directory.
    """
    for legacy_backup in config_path.parent.glob("karabiner_backup_*.json"):
        if legacy_backup.is_file():
            target = backup_dir / legacy_backup.name
            if not target.exists():
                shutil.move(legacy_backup, target)
            else:
                legacy_backup.unlink()


def cleanup_backups(backup_dir: Path, keep: int = MAX_BACKUPS) -> None:
    """Keep only the most recent backups.

    Args:
        backup_dir: Path to the backup directory.
        keep: Number of backups to keep.
    """
    backups = sorted(
        backup_dir.glob("karabiner_backup_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    for old_backup in backups[keep:]:
        old_backup.unlink()


def backup_config(path: Path | None = None) -> Path | None:
    """Backup the existing Karabiner configuration.

    Args:
        path: Path to the config file. Defaults to the standard location.

    Returns:
        Path to the backup file, or None if no backup was needed.
    """
    if path is None:
        path = DEFAULT_CONFIG_PATH

    if not path.exists():
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = path.parent / "automatic_backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    # Migrate legacy backups
    migrate_legacy_backups(path, backup_dir)

    backup_path = backup_dir / f"karabiner_backup_{timestamp}.json"
    shutil.copy2(path, backup_path)
    cleanup_backups(backup_dir)
    return backup_path


def list_backups(path: Path | None = None) -> list[Path]:
    """List available backups for the Karabiner configuration.

    Args:
        path: Path to the config file. Defaults to the standard location.

    Returns:
        A list of backup file paths, sorted newest first.
    """
    if path is None:
        path = DEFAULT_CONFIG_PATH

    backup_dir = path.parent / "automatic_backups"
    if not backup_dir.exists():
        return []

    return sorted(
        backup_dir.glob("karabiner_backup_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )


def restore_config(backup_path: Path, target_path: Path | None = None) -> bool:
    """Restore a Karabiner configuration from a backup.

    Args:
        backup_path: Path to the backup file to restore.
        target_path: Path to the config file. Defaults to the standard location.

    Returns:
        True if successful, False otherwise.
    """
    if target_path is None:
        target_path = DEFAULT_CONFIG_PATH

    if not backup_path.exists():
        return False

    try:
        shutil.copy2(backup_path, target_path)
        return True
    except Exception as e:
        print(f"❌ Error restoring backup: {e}")
        return False


def validate_json(json_str: str) -> bool:
    """Validate a JSON string.

    Args:
        json_str: The JSON string to validate.

    Returns:
        True if valid, False otherwise.
    """
    try:
        json.loads(json_str)
        return True
    except json.JSONDecodeError:
        return False


def validate_config(config_dict: dict[str, Any]) -> list[str]:
    """Validate a Karabiner configuration dictionary.

    Args:
        config_dict: The configuration dictionary to validate.

    Returns:
        List of validation errors (empty if valid).
    """
    errors: list[str] = []

    if "global" not in config_dict:
        errors.append("Missing 'global' key")

    if "profiles" not in config_dict:
        errors.append("Missing 'profiles' key")
    elif not isinstance(config_dict["profiles"], list):
        errors.append("'profiles' must be a list")
    elif len(config_dict["profiles"]) == 0:
        errors.append("At least one profile is required")

    return errors


def reload_karabiner() -> bool:
    """Reload Karabiner-Elements configuration.

    Returns:
        True if successful, False otherwise.
    """
    try:
        uid = os.getuid()
        subprocess.run(
            [
                "launchctl",
                "kickstart",
                "-k",
                f"gui/{uid}/org.pqrs.karabiner.karabiner_console_user_server",
            ],
            shell=False,
            check=True,
            capture_output=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Try alternative method
        try:
            uid = subprocess.check_output(["id", "-u"]).decode().strip()
            subprocess.run(
                [
                    "launchctl",
                    "kickstart",
                    "-k",
                    f"gui/{uid}/org.pqrs.karabiner.karabiner_console_user_server",
                ],
                shell=False,
                check=True,
                capture_output=True,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False


def show_diff(old_json: str, new_json: str, path: Path) -> None:
    """Show the difference between old and new configuration.

    Args:
        old_json: The existing configuration JSON string.
        new_json: The new configuration JSON string.
        path: The path to the configuration file.
    """
    diff = list(
        difflib.unified_diff(
            old_json.splitlines(keepends=True),
            new_json.splitlines(keepends=True),
            fromfile=f"a/{path.name}",
            tofile=f"b/{path.name}",
        )
    )

    if not diff:
        print("✨ No changes detected.")
        return

    print(f"🔍 Changes for {path}:")
    for line in diff:
        if line.startswith("+") and not line.startswith("+++"):
            print(f"\033[32m{line.rstrip()}\033[0m")  # Green
        elif line.startswith("-") and not line.startswith("---"):
            print(f"\033[31m{line.rstrip()}\033[0m")  # Red
        elif line.startswith("^"):
            print(f"\033[36m{line.rstrip()}\033[0m")  # Cyan
        else:
            print(line.rstrip())


def save_config(
    config: KarabinerConfig,
    path: Path | str | None = None,
    apply: bool = False,
    backup: bool = True,
    dry_run: bool = False,
) -> Path:
    """Save a Karabiner configuration to file.

    Args:
        config: The KarabinerConfig to save.
        path: Target path. Defaults to ~/.config/karabiner/karabiner.json
        apply: If True, reload Karabiner after saving.
        backup: If True, backup existing config before overwriting.
        dry_run: If True, show diff and don't write to file.

    Returns:
        The path where the config was saved (or would be saved).

    Raises:
        ValueError: If the generated JSON is invalid.
    """
    if path is None:
        path = DEFAULT_CONFIG_PATH
    elif isinstance(path, str):
        path = Path(path)

    # Build config
    config_dict = config.build()

    # Validate
    errors = validate_config(config_dict)
    if errors:
        raise ValueError(f"Invalid configuration: {', '.join(errors)}")

    json_str = json.dumps(config_dict, indent=2)
    if not validate_json(json_str):
        raise ValueError("Generated JSON is invalid")

    # Show diff if file exists
    if path.exists():
        old_json = path.read_text()
        if dry_run:
            show_diff(old_json, json_str, path)
            return path
        # In non-dry-run mode, we still might want to show diff if it's small?
        # For now, let's just focus on dry_run as requested.

    if dry_run:
        print(f"✨ New file would be created at {path}")
        print(json_str)
        return path

    # Backup existing config
    if backup and path.exists():
        backup_path = backup_config(path)
        if backup_path:
            print(f"📦 Backed up to {backup_path}")

    # Ensure directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    # Write config
    path.write_text(json_str)
    print(f"✅ Karabiner config written to {path}")

    # Reload if requested
    if apply:
        if reload_karabiner():
            print("🔄 Karabiner configuration reloaded")
        else:
            print("⚠️ Failed to reload Karabiner (try manually)")

    return path
