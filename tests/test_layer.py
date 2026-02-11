"""Tests for layer system."""

from __future__ import annotations

import pytest

from karabinerpyx import LayerStackBuilder, SimultaneousManipulator


class TestLayerStackBuilder:
    def test_single_trigger_activation(self):
        layer = LayerStackBuilder("hyper", "right_command")
        rules = layer.build_rules()

        activation_rule = rules[0].build()
        assert "hyper activation" in activation_rule["description"]

        manip = activation_rule["manipulators"][0]
        assert manip["from"]["key_code"] == "right_command"
        assert manip["to"][0]["set_variable"]["name"] == "hyper"
        assert manip["to"][0]["set_variable"]["value"] == 1
        assert manip["to_after_key_up"][0]["set_variable"]["value"] == 0

    def test_stacked_trigger_activation(self):
        layer = LayerStackBuilder("hyper_alt", ["right_command", "right_option"])
        rules = layer.build_rules()

        activation_rule = rules[0].build()
        assert "stacked activation" in activation_rule["description"]

        manip = activation_rule["manipulators"][0]
        assert "simultaneous" in manip["from"]
        assert len(manip["from"]["simultaneous"]) == 2

    def test_simple_mapping(self):
        layer = LayerStackBuilder("hyper", "right_command").map("j", "left_arrow")
        rules = layer.build_rules()

        mapping_rule = rules[1].build()
        assert "j -> left_arrow" in mapping_rule["description"]

        manip = mapping_rule["manipulators"][0]
        assert manip["from"]["key_code"] == "j"
        assert manip["to"][0]["key_code"] == "left_arrow"
        assert manip["conditions"][0]["name"] == "hyper"

    def test_dict_mapping(self):
        layer = LayerStackBuilder("hyper", "right_command").map(
            "j", {"key_code": "left_arrow", "repeat": False}
        )
        rules = layer.build_rules()

        mapping_rule = rules[1].build()
        manip = mapping_rule["manipulators"][0]

        assert manip["to"][0]["key_code"] == "left_arrow"
        assert manip["to"][0]["repeat"] is False

    def test_multiple_mappings(self):
        layer = (
            LayerStackBuilder("hyper", "right_command")
            .map("j", "left_arrow")
            .map("k", "down_arrow")
            .map("l", "right_arrow")
        )
        rules = layer.build_rules()
        assert len(rules) == 4

    def test_macro_mapping(self):
        layer = LayerStackBuilder("hyper", "right_command").map_macro(
            "t", template_type="typed_text", text="Hello!"
        )
        rules = layer.build_rules()

        macro_rule = rules[1].build()
        assert "macro" in macro_rule["description"]

        manip = macro_rule["manipulators"][0]
        assert "shell_command" in manip["to"][0]
        assert "Hello!" in manip["to"][0]["shell_command"]

    def test_combo_mapping(self):
        layer = LayerStackBuilder("hyper", "right_command").map_combo(
            ["j", "k"], "escape"
        )
        rules = layer.build_rules()

        combo_rule = rules[1].build()
        assert "combo" in combo_rule["description"]

        manip = combo_rule["manipulators"][0]
        assert "simultaneous" in manip["from"]

    def test_sequence_mapping(self):
        layer = LayerStackBuilder("hyper", "right_command").map_sequence(
            ["g", "g"], "home"
        )
        rules = layer.build_rules()

        assert len(rules) == 3

        seq_rule = rules[1].build()
        manip = seq_rule["manipulators"][0]
        assert "to_delayed_action" in manip

    def test_sequence_timeout(self):
        layer = (
            LayerStackBuilder("hyper", "right_command")
            .set_sequence_timeout(300)
            .map_sequence(["g", "g"], "home")
        )
        rules = layer.build_rules()

        seq_rule = rules[1].build()
        manip = seq_rule["manipulators"][0]
        assert manip["parameters"]["basic.to_delayed_action_delay_milliseconds"] == 300

    def test_app_condition(self):
        layer = (
            LayerStackBuilder("hyper", "right_command")
            .when_app("com.apple.Terminal")
            .map_macro("t", template_type="typed_text", text="Terminal!")
        )
        rules = layer.build_rules()

        macro_rule = rules[1].build()
        manip = macro_rule["manipulators"][0]

        assert len(manip["conditions"]) == 2
        app_cond = next(
            c for c in manip["conditions"] if c["type"] == "frontmost_application_if"
        )
        assert app_cond["bundle_identifiers"] == ["com.apple.Terminal"]

    def test_fluent_api(self):
        layer = (
            LayerStackBuilder("hyper", "right_command")
            .map("j", "left_arrow")
            .map("k", "down_arrow")
            .map_combo(["j", "k"], "escape")
            .map_macro("t", template_type="typed_text", text="Hi")
            .set_sequence_timeout(400)
            .map_sequence(["g", "g"], "home")
        )
        rules = layer.build_rules()
        assert len(rules) == 7

    def test_reject_empty_trigger(self):
        with pytest.raises(ValueError):
            LayerStackBuilder("bad", [])

    def test_reject_short_sequence(self):
        with pytest.raises(ValueError):
            LayerStackBuilder("bad", "caps_lock").map_sequence(["g"], "home")

    def test_reject_short_combo(self):
        with pytest.raises(ValueError):
            LayerStackBuilder("bad", "caps_lock").map_combo(["j"], "escape")


class TestSimultaneousManipulator:
    def test_build(self):
        manipulator = SimultaneousManipulator(["j", "k"], "escape", "hyper")
        result = manipulator.build()

        assert result["type"] == "basic"
        assert "simultaneous" in result["from"]
        assert len(result["from"]["simultaneous"]) == 2
        assert result["to"][0]["key_code"] == "escape"
        assert result["conditions"][0]["name"] == "hyper"

    def test_reject_short_combo(self):
        with pytest.raises(ValueError):
            SimultaneousManipulator(["j"], "escape", "hyper")
