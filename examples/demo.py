"""KarabinerPyX demo configuration."""

from __future__ import annotations

from pathlib import Path

from karabinerpyx import KarabinerConfig, LayerStackBuilder, Profile


def get_config() -> KarabinerConfig:
    """Build and return a complete Karabiner configuration."""
    hyper = (
        LayerStackBuilder("hyper", "right_command")
        .map("h", "left_arrow")
        .map("j", "down_arrow")
        .map("k", "up_arrow")
        .map("l", "right_arrow")
        .map_combo(["j", "k"], "escape")
        .set_sequence_timeout(300)
        .map_sequence(["g", "g"], "home")
        .map_macro("t", template_type="typed_text", text="Hello from KarabinerPyX")
    )

    alt = (
        LayerStackBuilder("alt", "right_option")
        .map("h", "home")
        .map("l", "end")
        .map("u", "page_up")
        .map("d", "page_down")
    )

    hyper_alt = (
        LayerStackBuilder("hyper_alt", ["right_command", "right_option"])
        .map("h", "left_arrow")
        .map("l", "right_arrow")
        .map_macro("t", template_type="typed_text", text="Stacked layer activated")
    )

    profile = Profile("KarabinerPyX Demo", selected=True)
    for layer in [hyper, alt, hyper_alt]:
        for rule in layer.build_rules():
            profile.add_rule(rule)

    return KarabinerConfig().add_profile(profile)


if __name__ == "__main__":
    config = get_config()
    output_path = Path(__file__).parent.parent / "karabiner_demo.json"
    config.save(path=output_path, apply=False)

    profile = config.profiles[0]
    print(f"Generated configuration with {len(profile.rules)} rules")
    for index, rule in enumerate(profile.rules, 1):
        print(f"  {index}. {rule.description}")

    print(f"Review output: {output_path}")
