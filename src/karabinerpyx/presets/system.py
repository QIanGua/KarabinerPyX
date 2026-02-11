from __future__ import annotations

from typing import TYPE_CHECKING

from karabinerpyx.models import Manipulator, Rule

if TYPE_CHECKING:
    from karabinerpyx.layer import LayerStackBuilder


def app_switcher_enhancement(
    from_key: str = "tab",
    to_key: str = "tab",
    modifiers: list[str] | None = None,
) -> Rule:
    """Create an app-switcher helper rule."""
    active_modifiers = modifiers or ["left_command"]

    rule = Rule("App Switcher Enhancement")
    manip = Manipulator(from_key).modifiers(mandatory=active_modifiers).to(to_key)
    return rule.add(manip)


def common_system_shortcuts(builder: LayerStackBuilder) -> LayerStackBuilder:
    """Add common macOS system shortcut key mappings."""
    return (
        builder.map("m", "mission_control")
        .map("s", "spotlight")
        .map("c", "control_center")
    )
