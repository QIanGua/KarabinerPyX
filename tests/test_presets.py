from __future__ import annotations

from karabinerpyx.layer import LayerStackBuilder
from karabinerpyx.models import KarabinerConfig, Profile
from karabinerpyx.presets import (
    app_switcher_enhancement,
    apply_presets,
    common_system_shortcuts,
    compose_presets,
    hyper_key_rule,
    vim_navigation,
)


def test_hyper_key_rule():
    rule = hyper_key_rule()
    assert "Hyper Key" in rule.description
    data = rule.build()
    assert data["manipulators"][0]["from"]["key_code"] == "caps_lock"
    assert data["manipulators"][0]["to"][0]["key_code"] == "right_command"


def test_app_switcher_enhancement():
    rule = app_switcher_enhancement()
    data = rule.build()
    manip = data["manipulators"][0]
    assert manip["from"]["key_code"] == "tab"
    assert manip["to"][0]["key_code"] == "tab"


def test_vim_navigation():
    builder = LayerStackBuilder("test", "right_command")
    vim_navigation(builder)
    rules = builder.build_rules()

    descriptions = [rule.description for rule in rules]
    assert any("h -> left_arrow" in description for description in descriptions)
    assert any("j -> down_arrow" in description for description in descriptions)
    assert any("k -> up_arrow" in description for description in descriptions)
    assert any("l -> right_arrow" in description for description in descriptions)


def test_common_system_shortcuts():
    builder = LayerStackBuilder("test", "right_command")
    common_system_shortcuts(builder)
    rules = builder.build_rules()

    descriptions = [rule.description for rule in rules]
    assert any("m -> mission_control" in description for description in descriptions)
    assert any("s -> spotlight" in description for description in descriptions)


def test_presets_integration():
    config = KarabinerConfig()
    profile = Profile("Preset Test")

    profile.add_rule(hyper_key_rule())

    nav_layer = LayerStackBuilder("nav", "right_command")
    apply_presets(nav_layer, vim_navigation, common_system_shortcuts)

    for rule in nav_layer.build_rules():
        profile.add_rule(rule)

    config.add_profile(profile)
    data = config.build()
    assert len(data["profiles"][0]["complex_modifications"]["rules"]) > 5


def test_compose_presets():
    builder = LayerStackBuilder("nav", "right_command")
    pipeline = compose_presets(vim_navigation, common_system_shortcuts)
    pipeline(builder)

    descriptions = [rule.description for rule in builder.build_rules()]
    assert any("h -> left_arrow" in description for description in descriptions)
    assert any("m -> mission_control" in description for description in descriptions)
