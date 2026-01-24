from __future__ import annotations

from karabinerpyx import KarabinerConfig, Profile, LayerStackBuilder
from karabinerpyx.presets import hyper_key_rule, vim_navigation, common_system_shortcuts


def get_config() -> KarabinerConfig:
    """A clean example using KarabinerPyX Presets."""
    config = KarabinerConfig()
    profile = Profile("Presets Demo")

    # 1. Map Caps Lock to Hyper (Right Command)
    # Tapping alone sends Escape
    profile.add_rule(hyper_key_rule(from_key="caps_lock", to_key="right_command", to_if_alone="escape"))

    # 2. Create a Layer triggered by Right Command
    hyper = LayerStackBuilder("hyper_layer", "right_command")
    
    # 3. Apply Vim Navigation Preset
    # Adds h,j,k,l navigation + u/d page up/down + 0/$ home/end
    vim_navigation(hyper)
    
    # 4. Apply Common System Shortcuts Preset
    # Adds m (Mission Control), s (Spotlight), c (Control Center)
    common_system_shortcuts(hyper)
    
    # Add rules to profile
    for rule in hyper.build_rules():
        profile.add_rule(rule)

    config.add_profile(profile)
    return config


if __name__ == "__main__":
    config = get_config()
    print("Presets Demo Configuration Generated.")
    # Show what would be generated
    config.save(dry_run=True)
