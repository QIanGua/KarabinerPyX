"""Advanced configuration example for KarabinerPyX.

This example demonstrates:
1. Multi-layered configuration.
2. Layer stacking (Hyper + Alt).
3. Application-specific layers.
4. Complex macros and sequences.
"""

from __future__ import annotations

from karabinerpyx import KarabinerConfig, Profile, LayerStackBuilder

def main():
    # 1. Initialize Config and Profile
    config = KarabinerConfig()
    profile = Profile("Production Profile")

    # 2. Define Hyper Layer (Right Command)
    # This is the primary navigation and utility layer
    hyper = LayerStackBuilder("hyper", "right_command")
    
    # Basic Navigation (Vim-style)
    hyper.map("h", "left_arrow")
    hyper.map("j", "down_arrow")
    hyper.map("k", "up_arrow")
    hyper.map("l", "right_arrow")
    
    # Quick Text Sequences
    hyper.map_sequence(["g", "g"], "home")
    hyper.map_sequence(["shift", "g"], "end")
    
    # App-specific mappings in Hyper layer
    # Only active when VS Code is frontmost
    hyper_vscode = LayerStackBuilder("hyper_vscode", "right_command").when_app("com.microsoft.VSCode")
    hyper_vscode.map("p", "p").map("command", "command")  # Example: Quick open

    # 3. Define Window Management Layer (Stacked: Hyper + Alt)
    # Triggered by holding both Right Command and Right Option
    window_mgmt = LayerStackBuilder("window_mgmt", ["right_command", "right_option"])
    
    # Map to Rectangle/Magnet shortcuts (assumes Cmd+Alt+Ctrl + Keys)
    def map_window(key: str, action: str):
        # Placeholder for complex modifier mapping
        # In a real scenario, you'd map to the specific shortcut of your window manager
        window_mgmt.map(key, action)

    window_mgmt.map("h", "left_arrow")  # Snap Left
    window_mgmt.map("l", "right_arrow") # Snap Right
    window_mgmt.map("f", "f")           # Fullscreen

    # 4. Developer Macros
    dev_macros = LayerStackBuilder("dev", "right_control")
    dev_macros.map_macro("c", template_type="typed_text", text="git commit -m \"\"")
    dev_macros.map_macro("p", template_type="typed_text", text="git push")
    dev_macros.map_macro("l", template_type="typed_text", text="console.log()")

    # 5. Build and Assemble
    for layer in [hyper, window_mgmt, dev_macros]:
        for rule in layer.build_rules():
            profile.add_rule(rule)

    config.add_profile(profile)

    # 6. Save (dry-run/print for example)
    print("Generated Advanced Configuration:")
    print(config.to_json())
    
    # To apply:
    # config.save(apply=True)

if __name__ == "__main__":
    main()
