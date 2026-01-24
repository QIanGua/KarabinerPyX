"""Core data models for Karabiner configuration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class Manipulator:
    """Base manipulator for key mappings."""

    def __init__(self, from_key: str):
        self.from_key = from_key
        self.to_keys: list[str] = []
        self.to_if_alone: list[str] = []
        self.to_if_held_down: list[str] = []
        self.conditions: list[dict[str, Any]] = []

    def to(self, *keys: str) -> Manipulator:
        """Add target keys."""
        self.to_keys.extend(keys)
        return self

    def if_alone(self, *keys: str) -> Manipulator:
        """Add to_if_alone keys."""
        self.to_if_alone.extend(keys)
        return self

    def if_held(self, *keys: str) -> Manipulator:
        """Add to_if_held_down keys."""
        self.to_if_held_down.extend(keys)
        return self

    def when_app(self, app_identifiers: str | list[str]) -> Manipulator:
        """Add app condition."""
        if isinstance(app_identifiers, str):
            app_identifiers = [app_identifiers]
        self.conditions.append(
            {
                "type": "frontmost_application_if",
                "bundle_identifiers": app_identifiers,
            }
        )
        return self

    def when_variable(self, var_name: str, value: int = 1) -> Manipulator:
        """Add variable condition."""
        self.conditions.append(
            {
                "type": "variable_if",
                "name": var_name,
                "value": value,
            }
        )
        return self

    def build(self) -> dict[str, Any]:
        """Build the manipulator dictionary."""
        manip: dict[str, Any] = {
            "type": "basic",
            "from": {"key_code": self.from_key},
        }
        if self.to_keys:
            manip["to"] = [{"key_code": k} for k in self.to_keys]
        if self.to_if_alone:
            manip["to_if_alone"] = [{"key_code": k} for k in self.to_if_alone]
        if self.to_if_held_down:
            manip["to_if_held_down"] = [{"key_code": k} for k in self.to_if_held_down]
        if self.conditions:
            manip["conditions"] = self.conditions
        return manip


class Rule:
    """A Karabiner rule containing manipulators."""

    def __init__(self, description: str):
        self.description = description
        self.manipulators: list[Manipulator] = []

    def add(self, manipulator: Manipulator) -> Rule:
        """Add a manipulator to the rule."""
        self.manipulators.append(manipulator)
        return self

    def extend(self, manipulators: list[Manipulator]) -> Rule:
        """Add multiple manipulators."""
        self.manipulators.extend(manipulators)
        return self

    def add_dict(self, manip_dict: dict[str, Any]) -> Rule:
        """Add a raw manipulator dictionary."""
        m = Manipulator("placeholder")
        m.build = lambda: manip_dict  # type: ignore[method-assign]
        self.manipulators.append(m)
        return self

    def build(self) -> dict[str, Any]:
        """Build the rule dictionary."""
        return {
            "description": self.description,
            "manipulators": [m.build() for m in self.manipulators],
        }


class Profile:
    """A Karabiner profile."""

    def __init__(self, name: str, selected: bool = True):
        self.name = name
        self.rules: list[Rule] = []
        self.selected = selected

    def add_rule(self, rule: Rule) -> Profile:
        """Add a rule to the profile."""
        self.rules.append(rule)
        return self

    def build(self) -> dict[str, Any]:
        """Build the profile dictionary."""
        return {
            "name": self.name,
            "selected": self.selected,
            "complex_modifications": {
                "rules": [r.build() for r in self.rules],
            },
        }


class KarabinerConfig:
    """Top-level Karabiner configuration."""

    DEFAULT_PATH = Path.home() / ".config" / "karabiner" / "karabiner.json"

    def __init__(self):
        self.profiles: list[Profile] = []
        self.global_settings: dict[str, Any] = {
            "check_for_updates_on_startup": True,
            "show_in_menu_bar": True,
            "show_profile_name_in_menu_bar": False,
        }

    def add_profile(self, profile: Profile) -> KarabinerConfig:
        """Add a profile to the configuration."""
        self.profiles.append(profile)
        return self

    def build(self) -> dict[str, Any]:
        """Build the configuration dictionary."""
        return {
            "global": self.global_settings,
            "profiles": [p.build() for p in self.profiles],
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.build(), indent=indent)

    def save(
        self,
        path: Path | str | None = None,
        apply: bool = False,
        backup: bool = True,
        dry_run: bool = False,
    ) -> Path:
        """Save configuration to file.

        Args:
            path: Target path. Defaults to ~/.config/karabiner/karabiner.json
            apply: If True, reload Karabiner after saving.
            backup: If True, backup existing config before overwriting.
            dry_run: If True, show diff and don't write to file.

        Returns:
            The path where the config was saved (or would be saved).
        """
        from karabinerpyx.deploy import save_config

        return save_config(self, path, apply=apply, backup=backup, dry_run=dry_run)
