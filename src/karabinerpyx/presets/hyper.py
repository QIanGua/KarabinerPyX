from __future__ import annotations

from karabinerpyx.models import Manipulator, Rule


def hyper_key_rule(
    from_key: str = "caps_lock",
    to_key: str = "right_command",
    to_if_alone: str = "escape",
) -> Rule:
    """Create a hyper-like key rule.

    Default behavior is caps_lock -> right_command when held,
    and escape when tapped alone.
    """
    rule = Rule(f"Hyper Key: {from_key} to {to_key}")
    manip = Manipulator(from_key).to(to_key)
    if to_if_alone:
        manip.if_alone(to_if_alone)
    return rule.add(manip)
