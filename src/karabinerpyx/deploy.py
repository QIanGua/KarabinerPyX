"""Runtime deployment utilities for Karabiner configuration."""

from __future__ import annotations

import difflib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from karabinerpyx.models import KarabinerConfig


DEFAULT_CONFIG_PATH = Path.home() / ".config" / "karabiner" / "karabiner.json"
MAX_BACKUPS = 10


@dataclass(frozen=True)
class SaveResult:
    """Result for a save operation."""

    path: Path
    backup_path: Path | None
    reload_status: bool | None
    diff_changed: bool
    dry_run: bool


def migrate_legacy_backups(config_path: Path, backup_dir: Path) -> None:
    """Migrate legacy backups from the config directory to the backup directory."""
    for legacy_backup in config_path.parent.glob("karabiner_backup_*.json"):
        if legacy_backup.is_file():
            target = backup_dir / legacy_backup.name
            if not target.exists():
                shutil.move(legacy_backup, target)
            else:
                legacy_backup.unlink()


def cleanup_backups(backup_dir: Path, keep: int = MAX_BACKUPS) -> None:
    """Keep only the most recent backups."""
    backups = sorted(
        backup_dir.glob("karabiner_backup_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for old_backup in backups[keep:]:
        old_backup.unlink()


def backup_config(path: Path | None = None) -> Path | None:
    """Backup the existing Karabiner configuration."""
    resolved_path = path or DEFAULT_CONFIG_PATH
    if not resolved_path.exists():
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = resolved_path.parent / "automatic_backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    migrate_legacy_backups(resolved_path, backup_dir)

    backup_path = backup_dir / f"karabiner_backup_{timestamp}.json"
    shutil.copy2(resolved_path, backup_path)
    cleanup_backups(backup_dir)
    return backup_path


def list_backups(path: Path | None = None) -> list[Path]:
    """List available backups for the Karabiner configuration."""
    resolved_path = path or DEFAULT_CONFIG_PATH
    backup_dir = resolved_path.parent / "automatic_backups"
    if not backup_dir.exists():
        return []

    return sorted(
        backup_dir.glob("karabiner_backup_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )


def restore_config(backup_path: Path, target_path: Path | None = None) -> bool:
    """Restore a Karabiner configuration from a backup."""
    resolved_target = target_path or DEFAULT_CONFIG_PATH
    if not backup_path.exists():
        return False

    try:
        resolved_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(backup_path, resolved_target)
    except OSError as exc:
        print(f"Error restoring backup: {exc}")
        return False
    return True


def validate_json(json_str: str) -> bool:
    """Validate a JSON string."""
    try:
        json.loads(json_str)
    except json.JSONDecodeError:
        return False
    return True


def validate_config(config_dict: dict[str, Any]) -> list[str]:
    """Validate a Karabiner configuration dictionary."""
    errors: list[str] = []

    if "global" not in config_dict:
        errors.append("Missing 'global' key")

    profiles = config_dict.get("profiles")
    if profiles is None:
        errors.append("Missing 'profiles' key")
    elif not isinstance(profiles, list):
        errors.append("'profiles' must be a list")
    elif not profiles:
        errors.append("At least one profile is required")

    return errors


def reload_karabiner() -> bool:
    """Reload Karabiner-Elements configuration."""
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
        try:
            uid_text = subprocess.check_output(["id", "-u"], text=True).strip()
            subprocess.run(
                [
                    "launchctl",
                    "kickstart",
                    "-k",
                    f"gui/{uid_text}/org.pqrs.karabiner.karabiner_console_user_server",
                ],
                shell=False,
                check=True,
                capture_output=True,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False


def _diff_lines(old_json: str, new_json: str, path: Path) -> list[str]:
    return list(
        difflib.unified_diff(
            old_json.splitlines(keepends=True),
            new_json.splitlines(keepends=True),
            fromfile=f"a/{path.name}",
            tofile=f"b/{path.name}",
        )
    )


def _should_colorize(color: bool | None) -> bool:
    if color is not None:
        return color
    return sys.stdout.isatty() and "NO_COLOR" not in os.environ


def _colorize_diff_line(line: str, enabled: bool) -> str:
    if not enabled:
        return line
    if line.startswith("+") and not line.startswith("+++"):
        return f"\033[32m{line}\033[0m"
    if line.startswith("-") and not line.startswith("---"):
        return f"\033[31m{line}\033[0m"
    return line


def show_diff(
    old_json: str, new_json: str, path: Path, color: bool | None = None
) -> bool:
    """Print a unified diff and return whether there are changes."""
    diff = _diff_lines(old_json, new_json, path)
    if not diff:
        print("No changes detected.")
        return False

    use_color = _should_colorize(color)
    print(f"Changes for {path}:")
    for line in diff:
        print(_colorize_diff_line(line.rstrip("\n"), use_color))
    return True


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
            tmp_path = Path(handle.name)
        tmp_path.replace(path)
    finally:
        if tmp_path and tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


def _resolve_path(path: Path | str | None) -> Path:
    if path is None:
        return DEFAULT_CONFIG_PATH
    if isinstance(path, str):
        return Path(path)
    return path


def save_config(
    config: KarabinerConfig,
    path: Path | str | None = None,
    apply: bool = False,
    backup: bool = True,
    dry_run: bool = False,
) -> SaveResult:
    """Save a Karabiner configuration and return structured result."""
    resolved_path = _resolve_path(path)
    config_dict = config.build()

    errors = validate_config(config_dict)
    if errors:
        raise ValueError(f"Invalid configuration: {', '.join(errors)}")

    json_str = json.dumps(config_dict, indent=2)
    if not validate_json(json_str):
        raise ValueError("Generated JSON is invalid")

    backup_path: Path | None = None
    old_json = ""
    has_existing = resolved_path.exists()
    if has_existing:
        old_json = resolved_path.read_text(encoding="utf-8")

    diff_changed = (not has_existing) or (old_json != json_str)

    if dry_run:
        if has_existing:
            show_diff(old_json, json_str, resolved_path, color=False)
        else:
            print(f"New file would be created at {resolved_path}")
            print(json_str)
        return SaveResult(
            path=resolved_path,
            backup_path=None,
            reload_status=None,
            diff_changed=diff_changed,
            dry_run=True,
        )

    if backup and has_existing:
        backup_path = backup_config(resolved_path)

    try:
        _atomic_write(resolved_path, json_str)
    except OSError as exc:
        if backup_path and backup_path.exists():
            shutil.copy2(backup_path, resolved_path)
        raise RuntimeError(f"Failed to write config atomically: {exc}") from exc

    reload_status: bool | None = None
    if apply:
        reload_status = reload_karabiner()

    return SaveResult(
        path=resolved_path,
        backup_path=backup_path,
        reload_status=reload_status,
        diff_changed=diff_changed,
        dry_run=False,
    )


def save_config_path(
    config: KarabinerConfig,
    path: Path | str | None = None,
    apply: bool = False,
    backup: bool = True,
    dry_run: bool = False,
) -> Path:
    """Compatibility wrapper that returns only path."""
    return save_config(config, path, apply=apply, backup=backup, dry_run=dry_run).path
