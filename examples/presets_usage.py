from __future__ import annotations

from karabinerpyx import KarabinerConfig, LayerStackBuilder, Profile
from karabinerpyx.presets import (
    apply_presets,
    common_system_shortcuts,
    hyper_key_rule,
    vim_navigation,
)


def get_config() -> KarabinerConfig:
    """A clean example using KarabinerPyX presets."""
    profile = Profile("Presets Demo")

    profile.add_rule(
        hyper_key_rule(
            from_key="caps_lock", to_key="right_command", to_if_alone="escape"
        )
    )

    hyper = LayerStackBuilder("hyper_layer", "right_command")
    apply_presets(hyper, vim_navigation, common_system_shortcuts)

    for rule in hyper.build_rules():
        profile.add_rule(rule)

    return KarabinerConfig().add_profile(profile)


if __name__ == "__main__":
    config = get_config()
    print("Presets demo configuration generated")
    config.save(dry_run=True)
