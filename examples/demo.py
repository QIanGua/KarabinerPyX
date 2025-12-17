"""KarabinerPyX Demo - Complete Usage Example.

This example demonstrates all features of KarabinerPyX:
- Layer system with single and multiple trigger keys
- Simple key mappings
- Combo (simultaneous) mappings
- Sequence mappings
- Macro mappings
- App conditions
"""

from pathlib import Path

from karabinerpyx import KarabinerConfig, LayerStackBuilder, Profile


def main():
    """Build and save a complete Karabiner configuration."""

    # ===========================================
    # Layer 1: Hyper Layer (Right Command)
    # ===========================================
    hyper = (
        LayerStackBuilder("hyper", "right_command")
        # Arrow keys: HJKL vim-style
        .map("h", "left_arrow")
        .map("j", "down_arrow")
        .map("k", "up_arrow")
        .map("l", "right_arrow")
        # Quick escape: J+K together
        .map_combo(["j", "k"], "escape")
        # Vim-style gg for Home
        .set_sequence_timeout(300)
        .map_sequence(["g", "g"], "home")
        # Quick text input
        .map_macro("t", template_type="typed_text", text="Hello from KarabinerPyX!")
    )

    # ===========================================
    # Layer 2: Alt Layer (Right Option)
    # ===========================================
    alt = (
        LayerStackBuilder("alt", "right_option")
        # Line navigation
        .map("h", "home")
        .map("l", "end")
        # Page navigation
        .map("u", "page_up")
        .map("d", "page_down")
    )

    # ===========================================
    # Layer 3: Stacked Layer (Hyper + Alt)
    # ===========================================
    hyper_alt = (
        LayerStackBuilder("hyper_alt", ["right_command", "right_option"])
        # Window management shortcuts (example)
        .map("h", "left_arrow")  # Would be used with modifiers in real setup
        .map("l", "right_arrow")
        # Quick macro for stacked layer
        .map_macro("t", template_type="typed_text", text="Stacked layer activated!")
    )

    # ===========================================
    # Build Profile
    # ===========================================
    profile = Profile("KarabinerPyX Demo", selected=True)

    # Add all layer rules
    for layer in [hyper, alt, hyper_alt]:
        for rule in layer.build_rules():
            profile.add_rule(rule)

    # ===========================================
    # Build and Save Config
    # ===========================================
    config = KarabinerConfig().add_profile(profile)

    # Save to current directory for demo (not the actual Karabiner location)
    output_path = Path(__file__).parent.parent / "karabiner_demo.json"
    config.save(path=output_path, apply=False)

    print(f"\n📝 Generated configuration with {len(profile.rules)} rules:")
    for i, rule in enumerate(profile.rules, 1):
        print(f"   {i}. {rule.description}")

    print(f"\n💡 To apply this configuration:")
    print(f"   1. Review: {output_path}")
    print(f"   2. Copy to: ~/.config/karabiner/karabiner.json")
    print(f"   3. Or use: config.save(apply=True)")


if __name__ == "__main__":
    main()
