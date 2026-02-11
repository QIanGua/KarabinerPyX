"""Core typed models for Karabiner configuration."""

from __future__ import annotations

import json
import warnings
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


class Buildable(Protocol):
    """Protocol for objects that can be compiled to Karabiner JSON."""

    def build(self) -> dict[str, Any]:
        """Compile to Karabiner JSON."""


@dataclass
class RawManipulator:
    """Validated wrapper for low-level manipulator dictionaries."""

    raw: dict[str, Any]

    def __init__(self, raw: Mapping[str, Any]):
        data = dict(raw)
        if not isinstance(data.get("type"), str):
            raise ValueError("Raw manipulator requires string field 'type'")
        if "from" not in data:
            raise ValueError("Raw manipulator requires field 'from'")
        self.raw = data

    def build(self) -> dict[str, Any]:
        """Return a defensive copy of raw manipulator data."""
        return deepcopy(self.raw)


@dataclass
class Manipulator:
    """Builder for Karabiner basic manipulators."""

    from_key: str
    mandatory_modifiers: list[str] = field(default_factory=list)
    optional_modifiers: list[str] = field(default_factory=list)
    to_keys: list[dict[str, Any]] = field(default_factory=list)
    to_if_alone: list[dict[str, Any]] = field(default_factory=list)
    to_if_held_down: list[dict[str, Any]] = field(default_factory=list)
    conditions: list[dict[str, Any]] = field(default_factory=list)

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

    def to_raw(self, action: Mapping[str, Any]) -> Manipulator:
        """Append a low-level action dictionary to 'to'."""
        self.to_keys.append(dict(action))
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
        apps = (
            [app_identifiers] if isinstance(app_identifiers, str) else app_identifiers
        )
        self.conditions.append(
            {
                "type": "frontmost_application_if",
                "bundle_identifiers": apps,
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
        apps = (
            [app_identifiers] if isinstance(app_identifiers, str) else app_identifiers
        )
        self.conditions.append(
            {
                "type": "frontmost_application_unless",
                "bundle_identifiers": apps,
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
        if not self.from_key:
            raise ValueError("from_key cannot be empty")

        from_dict: dict[str, Any] = {"key_code": self.from_key}
        if self.mandatory_modifiers or self.optional_modifiers:
            from_dict["modifiers"] = {}
            if self.mandatory_modifiers:
                from_dict["modifiers"]["mandatory"] = list(self.mandatory_modifiers)
            if self.optional_modifiers:
                from_dict["modifiers"]["optional"] = list(self.optional_modifiers)

        manip: dict[str, Any] = {
            "type": "basic",
            "from": from_dict,
        }
        if self.to_keys:
            manip["to"] = deepcopy(self.to_keys)
        if self.to_if_alone:
            manip["to_if_alone"] = deepcopy(self.to_if_alone)
        if self.to_if_held_down:
            manip["to_if_held_down"] = deepcopy(self.to_if_held_down)
        if self.conditions:
            manip["conditions"] = deepcopy(self.conditions)
        return manip


@dataclass
class Rule:
    """A Karabiner rule containing manipulators."""

    description: str
    manipulators: list[Buildable] = field(default_factory=list)

    def add(self, manipulator: Buildable) -> Rule:
        """Add a manipulator to the rule."""
        self.manipulators.append(manipulator)
        return self

    def extend(self, manipulators: list[Buildable]) -> Rule:
        """Add multiple manipulators."""
        self.manipulators.extend(manipulators)
        return self

    def add_raw(self, manip_dict: Mapping[str, Any]) -> Rule:
        """Add a raw manipulator dictionary with validation."""
        self.manipulators.append(RawManipulator(manip_dict))
        return self

    def add_dict(self, manip_dict: dict[str, Any]) -> Rule:
        """Compatibility shim for legacy API.

        Deprecated in v0.2. Use add_raw() instead.
        """
        warnings.warn(
            "Rule.add_dict() is deprecated; use Rule.add_raw() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.add_raw(manip_dict)

    def build(self) -> dict[str, Any]:
        """Build the rule dictionary."""
        return {
            "description": self.description,
            "manipulators": [m.build() for m in self.manipulators],
        }


@dataclass
class Profile:
    """A Karabiner profile."""

    name: str
    selected: bool = True
    rules: list[Rule] = field(default_factory=list)
    devices: list[dict[str, Any]] = field(default_factory=list)
    parameters: dict[str, Any] = field(default_factory=dict)
    virtual_hid_keyboard: dict[str, Any] = field(
        default_factory=lambda: {"country_code": 0}
    )

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
        """Add a device-specific configuration."""
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
        """Set profile-level parameters."""
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
            "devices": deepcopy(self.devices),
            "virtual_hid_keyboard": deepcopy(self.virtual_hid_keyboard),
        }
        if self.parameters:
            profile["complex_modifications"]["parameters"] = deepcopy(self.parameters)
        return profile


@dataclass
class KarabinerConfig:
    """Top-level Karabiner configuration."""

    DEFAULT_PATH = Path.home() / ".config" / "karabiner" / "karabiner.json"

    profiles: list[Profile] = field(default_factory=list)
    global_settings: dict[str, Any] = field(
        default_factory=lambda: {
            "check_for_updates_on_startup": True,
            "show_in_menu_bar": True,
            "show_profile_name_in_menu_bar": False,
        }
    )

    def add_profile(self, profile: Profile) -> KarabinerConfig:
        """Add a profile to the configuration."""
        self.profiles.append(profile)
        return self

    def build(self) -> dict[str, Any]:
        """Build the configuration dictionary."""
        return {
            "global": deepcopy(self.global_settings),
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
        """Compatibility save helper returning path for v0.1 callers."""
        from karabinerpyx.deploy import save_config_path

        warnings.warn(
            (
                "KarabinerConfig.save() returning Path is deprecated; "
                "use deploy.save_config()"
            ),
            DeprecationWarning,
            stacklevel=2,
        )
        return save_config_path(self, path, apply=apply, backup=backup, dry_run=dry_run)
