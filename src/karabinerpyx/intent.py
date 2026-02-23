"""Intent-based DSL for high-level Karabiner configuration authoring."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from karabinerpyx.models import KarabinerConfig


@dataclass
class IntentLayer:
    """High-level intent representation for one layer."""

    name: str
    trigger_keys: list[str]
    to_if_alone: str | None = None
    mappings: list[tuple[str, str | dict[str, Any]]] = field(default_factory=list)
    combos: list[tuple[list[str], str | list[dict[str, Any]], dict[str, Any]]] = (
        field(default_factory=list)
    )
    sequences: list[tuple[list[str], str, int]] = field(default_factory=list)
    macros: list[tuple[str, str, dict[str, Any]]] = field(default_factory=list)
    app_conditions_if: list[list[str]] = field(default_factory=list)
    app_conditions_unless: list[list[str]] = field(default_factory=list)
    raw_manipulators: list[tuple[str, dict[str, Any]]] = field(default_factory=list)

    def __init__(
        self,
        name: str,
        trigger: str | list[str],
        tap: str | None = None,
    ):
        if not name:
            raise ValueError("Layer name cannot be empty")

        trigger_keys = [trigger] if isinstance(trigger, str) else list(trigger)
        if not trigger_keys:
            raise ValueError("trigger cannot be empty")
        if any(not key for key in trigger_keys):
            raise ValueError("trigger cannot contain empty keys")

        self.name = name
        self.trigger_keys = trigger_keys
        self.to_if_alone = tap

        self.mappings = []
        self.combos = []
        self.sequences = []
        self.macros = []
        self.app_conditions_if = []
        self.app_conditions_unless = []
        self.raw_manipulators = []

    def map(self, from_key: str, to_key: str | dict[str, Any]) -> IntentLayer:
        """Add a simple in-layer key mapping."""
        if not from_key:
            raise ValueError("from_key cannot be empty")
        if isinstance(to_key, str) and not to_key:
            raise ValueError("to_key cannot be empty")
        self.mappings.append((from_key, to_key))
        return self

    def combo(
        self,
        keys: list[str],
        to_key: str | list[dict[str, Any]],
        **options: Any,
    ) -> IntentLayer:
        """Add simultaneous key mapping."""
        if len(keys) < 2:
            raise ValueError("keys must contain at least two keys")
        if any(not key for key in keys):
            raise ValueError("keys cannot contain empty values")
        if isinstance(to_key, str) and not to_key:
            raise ValueError("to_key cannot be empty")
        self.combos.append((keys, to_key, options))
        return self

    def sequence(
        self,
        keys: list[str],
        to_key: str,
        timeout_ms: int = 500,
    ) -> IntentLayer:
        """Add ordered key sequence mapping."""
        if len(keys) < 2:
            raise ValueError("keys must contain at least two keys")
        if any(not key for key in keys):
            raise ValueError("keys cannot contain empty values")
        if not to_key:
            raise ValueError("to_key cannot be empty")
        if timeout_ms <= 0:
            raise ValueError("timeout_ms must be positive")

        self.sequences.append((keys, to_key, timeout_ms))
        return self

    def macro(self, from_key: str, template: str, **params: Any) -> IntentLayer:
        """Add template-based macro mapping."""
        if not from_key:
            raise ValueError("from_key cannot be empty")
        if not template:
            raise ValueError("template cannot be empty")

        self.macros.append((from_key, template, params))
        return self

    def when_app(self, apps: str | list[str]) -> IntentLayer:
        """Enable the layer only for foreground apps."""
        app_list = [apps] if isinstance(apps, str) else list(apps)
        if not app_list or any(not app for app in app_list):
            raise ValueError("apps cannot be empty")
        self.app_conditions_if.append(app_list)
        return self

    def unless_app(self, apps: str | list[str]) -> IntentLayer:
        """Disable the layer for foreground apps."""
        app_list = [apps] if isinstance(apps, str) else list(apps)
        if not app_list or any(not app for app in app_list):
            raise ValueError("apps cannot be empty")
        self.app_conditions_unless.append(app_list)
        return self

    def add_raw(
        self,
        manipulator: Mapping[str, Any],
        description: str | None = None,
    ) -> IntentLayer:
        """Add a raw manipulator escape hatch without transformation."""
        desc = description or f"{self.name} raw"
        self.raw_manipulators.append((desc, dict(manipulator)))
        return self


@dataclass
class IntentProfile:
    """High-level intent representation for one profile."""

    name: str
    selected: bool = True
    dual_roles: list[tuple[str, str, str]] = field(default_factory=list)
    mappings: list[tuple[str, str | dict[str, Any]]] = field(default_factory=list)
    layers: list[IntentLayer] = field(default_factory=list)
    raw_manipulators: list[tuple[str, dict[str, Any]]] = field(default_factory=list)

    def dual_role(self, key: str, tap: str, hold: str) -> IntentProfile:
        """Add a dual-role mapping (tap action + hold modifier)."""
        if not key:
            raise ValueError("key cannot be empty")
        if not tap:
            raise ValueError("tap cannot be empty")
        if not hold:
            raise ValueError("hold cannot be empty")
        self.dual_roles.append((key, tap, hold))
        return self

    def layer(
        self,
        name: str,
        trigger: str | list[str],
        tap: str | None = None,
    ) -> IntentLayer:
        """Create and attach a new layer."""
        layer = IntentLayer(name=name, trigger=trigger, tap=tap)
        self.layers.append(layer)
        return layer

    def map(self, from_key: str, to_key: str | dict[str, Any]) -> IntentProfile:
        """Add a profile-level mapping."""
        if not from_key:
            raise ValueError("from_key cannot be empty")
        if isinstance(to_key, str) and not to_key:
            raise ValueError("to_key cannot be empty")
        self.mappings.append((from_key, to_key))
        return self

    def add_raw(
        self,
        manipulator: Mapping[str, Any],
        description: str = "intent raw",
    ) -> IntentProfile:
        """Add a raw manipulator escape hatch without transformation."""
        self.raw_manipulators.append((description, dict(manipulator)))
        return self


@dataclass
class IntentConfig:
    """Top-level intent-based DSL container."""

    profiles: list[IntentProfile] = field(default_factory=list)
    allow_shadow: bool = False

    def profile(self, name: str, selected: bool = True) -> IntentProfile:
        """Create and attach an intent profile."""
        if not name:
            raise ValueError("Profile name cannot be empty")
        profile = IntentProfile(name=name, selected=selected)
        self.profiles.append(profile)
        return profile

    def add_profile(self, profile: IntentProfile) -> IntentConfig:
        """Attach an existing intent profile object."""
        self.profiles.append(profile)
        return self

    def compile(self) -> KarabinerConfig:
        """Compile the intent model into low-level KarabinerConfig."""
        from karabinerpyx.compiler import compile_intent

        return compile_intent(self)
