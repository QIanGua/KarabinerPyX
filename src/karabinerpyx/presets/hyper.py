from __future__ import annotations

from karabinerpyx.models import Rule, Manipulator


def hyper_key_rule(
    from_key: str = "caps_lock",
    to_key: str = "right_command",
    to_if_alone: str = "escape",
) -> Rule:
    """Create a rule that maps a key to a Hyper Key.

    Default: caps_lock -> right_command (when held), escape (when tapped).

    Args:
        from_key: Key to map from.
        to_key: Modifier to act as.
        to_if_alone: Key to send if tapped alone.

    Returns:
        A Rule object.
    """
    rule = Rule(f"Hyper Key: {from_key} to {to_key}")
    manip = Manipulator(from_key).to(to_key)
    if to_if_alone:
        manip.if_alone(to_if_alone)
    rule.add(manip)
    return rule
