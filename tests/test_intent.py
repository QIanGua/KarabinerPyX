"""Tests for intent DSL and compiler behavior."""

from __future__ import annotations

import re

from karabinerpyx import IntentConfig, KarabinerConfig, LayerStackBuilder, Profile
from karabinerpyx.compiler import compile_intent


def test_intent_compiles_layer_and_profile():
    intent = IntentConfig()
    profile = intent.profile("Intent Demo")
    profile.dual_role("caps_lock", "escape", "left_control")
    profile.map("tab", "escape")

    layer = profile.layer("nav", "right_command", tap="right_command")
    layer.map("h", "left_arrow")
    layer.combo(["j", "k"], "escape")
    layer.sequence(["g", "g"], "home", timeout_ms=280)
    layer.macro("t", "typed_text", text="Hello")

    compiled = compile_intent(intent)
    built = compiled.build()

    rules = built["profiles"][0]["complex_modifications"]["rules"]
    descriptions = [rule["description"] for rule in rules]

    assert descriptions[0].startswith("Dual role")
    assert "Profile: tab -> escape" in descriptions[1]
    assert descriptions[2] == "nav activation"
    assert any("nav combo" in description for description in descriptions)
    assert any("nav sequence" in description for description in descriptions)
    assert descriptions[-1] == "nav macro: t -> typed_text"


def test_intent_sequence_uses_namespaced_variables():
    intent = IntentConfig()
    layer = intent.profile("My Profile").layer("Nav Layer", "right_command")
    layer.sequence(["g", "g"], "home")

    compiled = compile_intent(intent).build()
    rules = compiled["profiles"][0]["complex_modifications"]["rules"]

    seq_rules = [rule for rule in rules if "sequence" in rule["description"]]
    first = seq_rules[0]["manipulators"][0]
    var_name = first["to"][0]["set_variable"]["name"]

    assert re.match(
        r"^__kpyx_seq_my_profile_nav_layer_[0-9a-f]{8}_step1$",
        var_name,
    )


def test_intent_output_matches_legacy_layer_for_same_scenario():
    legacy_layer = LayerStackBuilder("nav", "right_command")
    legacy_layer.map("h", "left_arrow")
    legacy_layer.map("j", "down_arrow")

    legacy_profile = Profile("Golden")
    for rule in legacy_layer.build_rules():
        legacy_profile.add_rule(rule)
    legacy_config = KarabinerConfig().add_profile(legacy_profile)

    intent = IntentConfig()
    nav = intent.profile("Golden").layer("nav", "right_command")
    nav.map("h", "left_arrow")
    nav.map("j", "down_arrow")

    assert compile_intent(intent).build() == legacy_config.build()


def test_intent_add_raw_pass_through():
    intent = IntentConfig()
    layer = intent.profile("Raw").layer("raw_layer", "right_command")
    layer.add_raw(
        {
            "type": "basic",
            "from": {"key_code": "q"},
            "to": [{"key_code": "w"}],
        },
        description="raw custom",
    )

    compiled = compile_intent(intent).build()
    rules = compiled["profiles"][0]["complex_modifications"]["rules"]
    raw_rule = next(rule for rule in rules if rule["description"] == "raw custom")
    assert raw_rule["manipulators"][0]["from"]["key_code"] == "q"
