from __future__ import annotations

from collections.abc import Callable

from karabinerpyx.layer import LayerStackBuilder
from karabinerpyx.presets.hyper import hyper_key_rule
from karabinerpyx.presets.navigation import vim_navigation
from karabinerpyx.presets.system import (
    app_switcher_enhancement,
    common_system_shortcuts,
)

Preset = Callable[[LayerStackBuilder], LayerStackBuilder]


def apply_presets(builder: LayerStackBuilder, *presets: Preset) -> LayerStackBuilder:
    """Apply multiple presets to a builder in order."""
    result = builder
    for preset in presets:
        result = preset(result)
    return result


def compose_presets(*presets: Preset) -> Preset:
    """Compose multiple presets into one preset function."""

    def _composed(builder: LayerStackBuilder) -> LayerStackBuilder:
        return apply_presets(builder, *presets)

    return _composed


__all__ = [
    "Preset",
    "apply_presets",
    "compose_presets",
    "hyper_key_rule",
    "vim_navigation",
    "common_system_shortcuts",
    "app_switcher_enhancement",
]
