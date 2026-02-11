from __future__ import annotations

from karabinerpyx import LayerStackBuilder, Manipulator, Profile


def test_advanced_profile_settings():
    profile = Profile("Advanced")
    profile.add_device(
        vendor_id=1278, product_id=514, disable_built_in_keyboard_if_exists=True
    )
    profile.set_parameters(**{"basic.simultaneous_threshold_milliseconds": 50})
    profile.set_virtual_keyboard(country_code=0)

    data = profile.build()
    assert data["devices"][0]["identifiers"]["vendor_id"] == 1278
    assert data["devices"][0]["disable_built_in_keyboard_if_exists"] is True
    assert (
        data["complex_modifications"]["parameters"][
            "basic.simultaneous_threshold_milliseconds"
        ]
        == 50
    )
    assert data["virtual_hid_keyboard"]["country_code"] == 0


def test_unless_conditions():
    manip = (
        Manipulator("a")
        .to("b")
        .unless_app("com.apple.Terminal")
        .unless_variable("debug", 1)
    )
    data = manip.build()

    cond_types = [c["type"] for c in data["conditions"]]
    assert "frontmost_application_unless" in cond_types
    assert "variable_unless" in cond_types

    # Layer unless
    layer = LayerStackBuilder("test", "cmd").unless_app("com.apple.Finder")
    rules = layer.build_rules()
    for rule in rules:
        if "activation" not in rule.description:
            r_data = rule.build()
            assert any(
                c["type"] == "frontmost_application_unless"
                for c in r_data["manipulators"][0]["conditions"]
            )


def test_advanced_simultaneous():
    layer = LayerStackBuilder("test", "cmd")
    layer.map_combo(
        ["w", "i"],
        to_key=[{"shell_command": "echo 1"}],
        key_down_order="strict",
        to_after_key_up=[{"set_variable": {"name": "test", "value": 0}}],
    )

    rules = layer.build_rules()
    combo_rule = [r for r in rules if "combo" in r.description][0]
    data = combo_rule.build()["manipulators"][0]

    assert data["from"]["simultaneous_options"]["key_down_order"] == "strict"
    assert data["to_after_key_up"][0]["set_variable"]["name"] == "test"
