"""Tests for layer system."""

from karabinerpyx import LayerStackBuilder, SimultaneousManipulator


class TestLayerStackBuilder:
    """Tests for LayerStackBuilder class."""

    def test_single_trigger_activation(self):
        """Test single trigger key layer activation."""
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
        """Test multiple trigger keys layer activation."""
        layer = LayerStackBuilder("hyper_alt", ["right_command", "right_option"])
        rules = layer.build_rules()

        activation_rule = rules[0].build()
        assert "stacked activation" in activation_rule["description"]

        manip = activation_rule["manipulators"][0]
        assert "simultaneous" in manip["from"]
        assert len(manip["from"]["simultaneous"]) == 2

    def test_simple_mapping(self):
        """Test simple key mapping within layer."""
        layer = LayerStackBuilder("hyper", "right_command").map("j", "left_arrow")
        rules = layer.build_rules()

        # Second rule should be the mapping
        mapping_rule = rules[1].build()
        assert "j → left_arrow" in mapping_rule["description"]

        manip = mapping_rule["manipulators"][0]
        assert manip["from"]["key_code"] == "j"
        assert manip["to"][0]["key_code"] == "left_arrow"
        assert manip["conditions"][0]["name"] == "hyper"

    def test_dict_mapping(self):
        """Test mapping to raw dict action."""
        layer = LayerStackBuilder("hyper", "right_command").map(
            "j", {"key_code": "left_arrow", "repeat": False}
        )
        rules = layer.build_rules()

        mapping_rule = rules[1].build()
        manip = mapping_rule["manipulators"][0]

        assert manip["to"][0]["key_code"] == "left_arrow"
        assert manip["to"][0]["repeat"] is False

    def test_multiple_mappings(self):
        """Test multiple mappings."""
        layer = (
            LayerStackBuilder("hyper", "right_command")
            .map("j", "left_arrow")
            .map("k", "down_arrow")
            .map("l", "right_arrow")
        )
        rules = layer.build_rules()

        # 1 activation + 3 mappings
        assert len(rules) == 4

    def test_macro_mapping(self):
        """Test macro mapping."""
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
        """Test combo (simultaneous) mapping."""
        layer = LayerStackBuilder("hyper", "right_command").map_combo(
            ["j", "k"], "escape"
        )
        rules = layer.build_rules()

        combo_rule = rules[1].build()
        assert "combo" in combo_rule["description"]

        manip = combo_rule["manipulators"][0]
        assert "simultaneous" in manip["from"]

    def test_sequence_mapping(self):
        """Test sequence mapping."""
        layer = LayerStackBuilder("hyper", "right_command").map_sequence(
            ["g", "g"], "home"
        )
        rules = layer.build_rules()

        # Activation + 2 sequence steps
        assert len(rules) == 3

        # Check sequence uses delayed_action
        seq_rule = rules[1].build()
        manip = seq_rule["manipulators"][0]
        assert "to_delayed_action" in manip

    def test_sequence_timeout(self):
        """Test sequence timeout configuration."""
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
        """Test app condition on layer."""
        layer = (
            LayerStackBuilder("hyper", "right_command")
            .when_app("com.apple.Terminal")
            .map_macro("t", template_type="typed_text", text="Terminal!")
        )
        rules = layer.build_rules()

        macro_rule = rules[1].build()
        manip = macro_rule["manipulators"][0]

        # Should have both variable and app conditions
        assert len(manip["conditions"]) == 2
        app_cond = next(
            c for c in manip["conditions"] if c["type"] == "frontmost_application_if"
        )
        assert app_cond["bundle_identifiers"] == ["com.apple.Terminal"]

    def test_fluent_api(self):
        """Test fluent API chaining."""
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

        # 1 activation + 2 mappings + 1 combo + 1 macro + 2 sequence steps
        assert len(rules) == 7


class TestSimultaneousManipulator:
    """Tests for SimultaneousManipulator class."""

    def test_build(self):
        """Test simultaneous manipulator building."""
        m = SimultaneousManipulator(["j", "k"], "escape", "hyper")
        result = m.build()

        assert result["type"] == "basic"
        assert "simultaneous" in result["from"]
        assert len(result["from"]["simultaneous"]) == 2
        assert result["to"][0]["key_code"] == "escape"
        assert result["conditions"][0]["name"] == "hyper"
