"""Advanced configuration example for KarabinerPyX.

This example demonstrates:
1. Multi-layered configuration.
2. Layer stacking (Hyper + Alt).
3. Application-specific layers.
4. Complex macros and sequences.
"""

from __future__ import annotations

from karabinerpyx import KarabinerConfig, Profile, LayerStackBuilder
from karabinerpyx.presets import hyper_key_rule, vim_navigation, common_system_shortcuts


def get_config() -> KarabinerConfig:
    # 1. Initialize Config and Profile
    config = KarabinerConfig()
    profile = Profile("Production Profile")

    # 2. Add Hyper Key (Caps Lock -> Right Command)
    profile.add_rule(hyper_key_rule("caps_lock", "right_command"))

    # 3. Define Hyper Layer (Right Command)
    # This is the primary navigation and utility layer
    hyper = LayerStackBuilder("hyper", "right_command")
    
    # Use Presets for Navigation and System Shortcuts
    vim_navigation(hyper)
    common_system_shortcuts(hyper)
    
    # Custom mappings in Hyper layer
    hyper.map_sequence(["shift", "g"], "end")
    
    # App-specific mappings in Hyper layer
    # Only active when VS Code is frontmost
    hyper_vscode = LayerStackBuilder("hyper_vscode", "right_command").when_app("com.microsoft.VSCode")
    hyper_vscode.map("p", "p")  # Example: Quick open

    # 4. Define Window Management Layer (Stacked: Hyper + Alt)
    # Triggered by holding both Right Command and Right Option
    window_mgmt = LayerStackBuilder("window_mgmt", ["right_command", "right_option"])
    
    window_mgmt.map("h", "left_arrow")  # Snap Left
    window_mgmt.map("l", "right_arrow") # Snap Right
    window_mgmt.map("f", "f")           # Fullscreen

    # 5. Developer Macros
    dev_macros = LayerStackBuilder("dev", "right_control")
    dev_macros.map_macro("c", template_type="typed_text", text="git commit -m \"\"")
    dev_macros.map_macro("p", template_type="typed_text", text="git push")
    dev_macros.map_macro("l", template_type="typed_text", text="console.log()")

    # 6. Build and Assemble
    for layer in [hyper, hyper_vscode, window_mgmt, dev_macros]:
        for rule in layer.build_rules():
            profile.add_rule(rule)

    config.add_profile(profile)
    return config


def main():
    config = get_config()
    # 7. Save (dry-run/print for example)
    print("Generated Advanced Configuration:")
    config.save(dry_run=True)
    
    # To apply:
    # config.save(apply=True)

if __name__ == "__main__":
    main()
