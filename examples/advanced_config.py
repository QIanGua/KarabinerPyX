"""Advanced configuration example for KarabinerPyX."""

from __future__ import annotations

from karabinerpyx import KarabinerConfig, LayerStackBuilder, Profile
from karabinerpyx.presets import (
    apply_presets,
    common_system_shortcuts,
    hyper_key_rule,
    vim_navigation,
)


def get_config() -> KarabinerConfig:
    config = KarabinerConfig()
    profile = Profile("Production Profile")

    profile.add_rule(hyper_key_rule("caps_lock", "right_command"))

    hyper = LayerStackBuilder("hyper", "right_command")
    apply_presets(hyper, vim_navigation, common_system_shortcuts)
    hyper.map_sequence(["g", "g"], "end")

    hyper_vscode = LayerStackBuilder("hyper_vscode", "right_command").when_app(
        "com.microsoft.VSCode"
    )
    hyper_vscode.map("p", "p")

    window_mgmt = LayerStackBuilder("window_mgmt", ["right_command", "right_option"])
    window_mgmt.map("h", "left_arrow")
    window_mgmt.map("l", "right_arrow")
    window_mgmt.map("f", "f")

    dev_macros = LayerStackBuilder("dev", "right_control")
    dev_macros.map_macro("c", template_type="typed_text", text='git commit -m ""')
    dev_macros.map_macro("p", template_type="typed_text", text="git push")
    dev_macros.map_macro("l", template_type="typed_text", text="console.log()")

    for layer in [hyper, hyper_vscode, window_mgmt, dev_macros]:
        for rule in layer.build_rules():
            profile.add_rule(rule)

    config.add_profile(profile)
    return config


def main() -> None:
    config = get_config()
    print("Generated advanced configuration")
    config.save(dry_run=True)


if __name__ == "__main__":
    main()
