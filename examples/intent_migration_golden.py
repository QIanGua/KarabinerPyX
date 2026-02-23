"""Golden-equivalence example between legacy builder API and intent DSL."""

from __future__ import annotations

from karabinerpyx import IntentConfig, KarabinerConfig, LayerStackBuilder, Profile
from karabinerpyx.compiler import compile_intent


def build_legacy() -> KarabinerConfig:
    nav = LayerStackBuilder("nav", "right_command")
    nav.map("h", "left_arrow")
    nav.map("j", "down_arrow")

    profile = Profile("Golden")
    for rule in nav.build_rules():
        profile.add_rule(rule)

    return KarabinerConfig().add_profile(profile)


def build_intent() -> IntentConfig:
    intent = IntentConfig()
    nav = intent.profile("Golden").layer("nav", "right_command")
    nav.map("h", "left_arrow")
    nav.map("j", "down_arrow")
    return intent


if __name__ == "__main__":
    legacy = build_legacy().build()
    intent = compile_intent(build_intent()).build()
    print("Equivalent:", legacy == intent)
