from __future__ import annotations

from typing import TYPE_CHECKING
from karabinerpyx.models import Rule, Manipulator

if TYPE_CHECKING:
    from karabinerpyx.layer import LayerStackBuilder


def app_switcher_enhancement(
    from_key: str = "tab", to_key: str = "tab", modifiers: list[str] | None = None
) -> Rule:
    """Enhance Cmd+Tab or Alt+Tab switching.

    This is just a placeholder example for now.
    """
    if modifiers is None:
        modifiers = ["left_command"]

    rule = Rule("App Switcher Enhancement")
    manip = (
        Manipulator(from_key).to(to_key).when_app(["com.apple.Switcher"])
    )  # Just an example
    rule.add(manip)
    return rule


def common_system_shortcuts(builder: LayerStackBuilder) -> LayerStackBuilder:
    """Add common system shortcuts to a layer.

    Example:
        m -> mission_control
        s -> spotlight
        c -> control_center
    """
    return (
        builder.map("m", "mission_control")
        .map("s", "spotlight")
        .map("c", "control_center")
    )
