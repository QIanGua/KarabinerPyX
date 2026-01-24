from __future__ import annotations

from karabinerpyx.models import KarabinerConfig, Profile
from karabinerpyx.layer import LayerStackBuilder
from karabinerpyx.presets import hyper_key_rule, vim_navigation, common_system_shortcuts


def test_hyper_key_rule():
    rule = hyper_key_rule()
    assert "Hyper Key" in rule.description
    data = rule.build()
    assert data["manipulators"][0]["from"]["key_code"] == "caps_lock"
    assert data["manipulators"][0]["to"][0]["key_code"] == "right_command"


def test_vim_navigation():
    builder = LayerStackBuilder("test", "right_command")
    vim_navigation(builder)
    rules = builder.build_rules()

    # Check if arrow keys are mapped
    descriptions = [r.description for r in rules]
    assert any("h → left_arrow" in d for d in descriptions)
    assert any("j → down_arrow" in d for d in descriptions)
    assert any("k → up_arrow" in d for d in descriptions)
    assert any("l → right_arrow" in d for d in descriptions)


def test_common_system_shortcuts():
    builder = LayerStackBuilder("test", "right_command")
    common_system_shortcuts(builder)
    rules = builder.build_rules()

    descriptions = [r.description for r in rules]
    assert any("m → mission_control" in d for d in descriptions)
    assert any("s → spotlight" in d for d in descriptions)


def test_presets_integration():
    config = KarabinerConfig()
    profile = Profile("Preset Test")

    # Add Hyper Key
    profile.add_rule(hyper_key_rule())

    # Add Navigation Layer
    nav_layer = LayerStackBuilder("nav", "right_command")
    vim_navigation(nav_layer)
    common_system_shortcuts(nav_layer)

    for rule in nav_layer.build_rules():
        profile.add_rule(rule)

    config.add_profile(profile)
    data = config.build()

    assert len(data["profiles"][0]["complex_modifications"]["rules"]) > 5
