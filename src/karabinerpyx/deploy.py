"""Deployment utilities for Karabiner configuration."""

from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from karabinerpyx.models import KarabinerConfig

# Default Karabiner config path
DEFAULT_CONFIG_PATH = Path.home() / ".config" / "karabiner" / "karabiner.json"


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
    backup_path = path.parent / f"karabiner_backup_{timestamp}.json"
    shutil.copy2(path, backup_path)
    return backup_path


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
        subprocess.run(
            [
                "launchctl",
                "kickstart",
                "-k",
                "gui/$(id -u)/org.pqrs.karabiner.karabiner_console_user_server",
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


def save_config(
    config: KarabinerConfig,
    path: Path | str | None = None,
    apply: bool = False,
    backup: bool = True,
) -> Path:
    """Save a Karabiner configuration to file.

    Args:
        config: The KarabinerConfig to save.
        path: Target path. Defaults to ~/.config/karabiner/karabiner.json
        apply: If True, reload Karabiner after saving.
        backup: If True, backup existing config before overwriting.

    Returns:
        The path where the config was saved.

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
