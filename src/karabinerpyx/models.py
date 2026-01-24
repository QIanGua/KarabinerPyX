"""Core data models for Karabiner configuration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class Manipulator:
    """Base manipulator for key mappings."""

    def __init__(self, from_key: str):
        self.from_key = from_key
        self.mandatory_modifiers: list[str] = []
        self.optional_modifiers: list[str] = []
        self.to_keys: list[str | dict[str, Any]] = []
        self.to_if_alone: list[str | dict[str, Any]] = []
        self.to_if_held_down: list[str | dict[str, Any]] = []
        self.conditions: list[dict[str, Any]] = []

    def modifiers(
        self, mandatory: list[str] | None = None, optional: list[str] | None = None
    ) -> Manipulator:
        """Set mandatory and optional modifiers for 'from'."""
        if mandatory:
            self.mandatory_modifiers.extend(mandatory)
        if optional:
            self.optional_modifiers.extend(optional)
        return self

    def to(
        self, key: str, modifiers: list[str] | None = None, **extra: Any
    ) -> Manipulator:
        """Add target key with optional modifiers."""
        target: dict[str, Any] = {"key_code": key}
        if modifiers:
            target["modifiers"] = modifiers
        target.update(extra)
        self.to_keys.append(target)
        return self

    def if_alone(
        self, key: str, modifiers: list[str] | None = None, **extra: Any
    ) -> Manipulator:
        """Add to_if_alone key with optional modifiers."""
        target: dict[str, Any] = {"key_code": key}
        if modifiers:
            target["modifiers"] = modifiers
        target.update(extra)
        self.to_if_alone.append(target)
        return self

    def if_held(
        self, key: str, modifiers: list[str] | None = None, **extra: Any
    ) -> Manipulator:
        """Add to_if_held_down key with optional modifiers."""
        target: dict[str, Any] = {"key_code": key}
        if modifiers:
            target["modifiers"] = modifiers
        target.update(extra)
        self.to_if_held_down.append(target)
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

    def unless_app(self, app_identifiers: str | list[str]) -> Manipulator:
        """Exclude specific apps from this mapping."""
        if isinstance(app_identifiers, str):
            app_identifiers = [app_identifiers]
        self.conditions.append(
            {
                "type": "frontmost_application_unless",
                "bundle_identifiers": app_identifiers,
            }
        )
        return self

    def unless_variable(self, var_name: str, value: int = 1) -> Manipulator:
        """Exclude this mapping if a variable has a specific value."""
        self.conditions.append(
            {
                "type": "variable_unless",
                "name": var_name,
                "value": value,
            }
        )
        return self

    def build(self) -> dict[str, Any]:
        """Build the manipulator dictionary."""
        from_dict: dict[str, Any] = {"key_code": self.from_key}
        if self.mandatory_modifiers or self.optional_modifiers:
            from_dict["modifiers"] = {}
            if self.mandatory_modifiers:
                from_dict["modifiers"]["mandatory"] = self.mandatory_modifiers
            if self.optional_modifiers:
                from_dict["modifiers"]["optional"] = self.optional_modifiers

        manip: dict[str, Any] = {
            "type": "basic",
            "from": from_dict,
        }
        if self.to_keys:
            manip["to"] = [
                {"key_code": k} if isinstance(k, str) else k for k in self.to_keys
            ]
        if self.to_if_alone:
            manip["to_if_alone"] = [
                {"key_code": k} if isinstance(k, str) else k for k in self.to_if_alone
            ]
        if self.to_if_held_down:
            manip["to_if_held_down"] = [
                {"key_code": k} if isinstance(k, str) else k
                for k in self.to_if_held_down
            ]
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
        self.devices: list[dict[str, Any]] = []
        self.parameters: dict[str, Any] = {}
        self.virtual_hid_keyboard: dict[str, Any] = {"country_code": 0}

    def add_rule(self, rule: Rule) -> Profile:
        """Add a rule to the profile."""
        self.rules.append(rule)
        return self

    def add_device(
        self,
        vendor_id: int,
        product_id: int,
        disable_built_in_keyboard_if_exists: bool = False,
        **extra: Any,
    ) -> Profile:
        """Add a device-specific configuration.

        Args:
            vendor_id: Vendor ID of the device.
            product_id: Product ID of the device.
            disable_built_in_keyboard_if_exists: Whether to disable built-in keyboard.
            **extra: Extra device-specific settings.
        """
        device = {
            "identifiers": {
                "vendor_id": vendor_id,
                "product_id": product_id,
                "is_keyboard": extra.pop("is_keyboard", True),
                "is_pointing_device": extra.pop("is_pointing_device", False),
            },
            "disable_built_in_keyboard_if_exists": disable_built_in_keyboard_if_exists,
        }
        device.update(extra)
        self.devices.append(device)
        return self

    def set_parameters(self, **parameters: Any) -> Profile:
        """Set profile-level parameters.

        Common parameters:
            basic.simultaneous_threshold_milliseconds: int
            basic.to_if_alone_timeout_milliseconds: int
            basic.to_if_held_down_threshold_milliseconds: int
            basic.to_delayed_action_delay_milliseconds: int
        """
        self.parameters.update(parameters)
        return self

    def set_virtual_keyboard(self, country_code: int = 0) -> Profile:
        """Set virtual HID keyboard configuration."""
        self.virtual_hid_keyboard = {"country_code": country_code}
        return self

    def build(self) -> dict[str, Any]:
        """Build the profile dictionary."""
        profile: dict[str, Any] = {
            "name": self.name,
            "selected": self.selected,
            "complex_modifications": {
                "rules": [r.build() for r in self.rules],
            },
            "devices": self.devices,
            "virtual_hid_keyboard": self.virtual_hid_keyboard,
        }
        if self.parameters:
            profile["complex_modifications"]["parameters"] = self.parameters
        return profile


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
