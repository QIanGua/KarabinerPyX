"""Complex scenario integration tests."""

from __future__ import annotations
from karabinerpyx import LayerStackBuilder


class TestComplexScenarios:
    """Test suite for complex layering and stacking scenarios."""

    def test_stacked_layer_activation(self):
        """Test that stacked layers (multiple trigger keys) generate correct activation rules."""
        layer = LayerStackBuilder("stacked", ["left_shift", "left_control"])
        rules = layer.build_rules()

        # Find activation rule
        activation_rule = next(
            r for r in rules if "stacked activation" in r.description
        )
        manip = activation_rule.manipulators[0].build()

        assert "simultaneous" in manip["from"]
        assert len(manip["from"]["simultaneous"]) == 2
        assert manip["to"][0]["set_variable"]["name"] == "stacked"
        assert manip["to"][0]["set_variable"]["value"] == 1

    def test_nested_layer_conditions(self):
        """Test that mappings within a layer inherit both layer and app conditions."""
        layer = LayerStackBuilder("hyper", "right_command")
        layer.when_app("com.apple.Terminal")
        layer.map("j", "down_arrow")

        rules = layer.build_rules()
        mapping_rule = next(
            r for r in rules if "hyper: j → down_arrow" in r.description
        )
        manip = mapping_rule.manipulators[0].build()

        # Should have 2 conditions: variable_if (layer) and frontmost_application_if (app)
        cond_types = [c["type"] for c in manip["conditions"]]
        assert "variable_if" in cond_types
        assert "frontmost_application_if" in cond_types

        app_cond = next(
            c for c in manip["conditions"] if c["type"] == "frontmost_application_if"
        )
        assert "com.apple.Terminal" in app_cond["bundle_identifiers"]

    def test_sequence_reset_logic(self):
        """Test that sequence mappings have correct reset (to_if_canceled) logic."""
        layer = LayerStackBuilder("nav", "fn")
        layer.map_sequence(["g", "g"], "home")

        rules = layer.build_rules()
        # Sequence rules are generated for each step
        seq_rules = [r for r in rules if "nav sequence" in r.description]
        assert len(seq_rules) == 2

        # Check first step (g)
        step1_manip = seq_rules[0].manipulators[0].build()
        assert "to_delayed_action" in step1_manip
        canceled_actions = step1_manip["to_delayed_action"]["to_if_canceled"]

        # Should reset current step variable
        reset_vars = [a["set_variable"]["name"] for a in canceled_actions]
        assert any("step1" in v for v in reset_vars)

    def test_macro_with_params(self):
        """Test macro mapping with template parameters."""
        layer = LayerStackBuilder("macros", "right_command")
        layer.map_macro("t", template_type="typed_text", text="hello")

        rules = layer.build_rules()
        macro_rule = next(r for r in rules if "macros macro: t" in r.description)
        manip = macro_rule.manipulators[0].build()

        # Check shell_command (mocked via make_shell_command)
        assert "to" in manip
        assert "shell_command" in manip["to"][0]
        # In the current implementation, make_shell_command is imported from templates.py
        # We assume it correctly fills the template.
