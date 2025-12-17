"""Integration tests for the complete workflow."""

import json
import tempfile
from pathlib import Path

import pytest
from karabinerpyx import (
    KarabinerConfig,
    LayerStackBuilder,
    Manipulator,
    Profile,
    Rule,
)


class TestFullWorkflow:
    """Test complete configuration workflow."""

    def test_readme_example(self):
        """Test the example from README.md works correctly."""
        # Build layers
        hyper = (
            LayerStackBuilder("hyper", "right_command")
            .map("j", "left_arrow")
            .map("k", "down_arrow")
            .map_macro("t", template_type="typed_text", text="Hello from KarabinerPyX!")
        )

        # Build profile
        profile = Profile("KarabinerPyX Demo")
        for rule in hyper.build_rules():
            profile.add_rule(rule)

        # Build config
        config = KarabinerConfig().add_profile(profile)
        result = config.build()

        # Validate structure
        assert "global" in result
        assert "profiles" in result
        assert len(result["profiles"]) == 1
        assert result["profiles"][0]["name"] == "KarabinerPyX Demo"

        rules = result["profiles"][0]["complex_modifications"]["rules"]
        assert len(rules) == 4  # activation + 2 mappings + 1 macro

    def test_multiple_layers(self):
        """Test multiple layers in one config."""
        # Single layers
        hyper = (
            LayerStackBuilder("hyper", "right_command")
            .map("j", "left_arrow")
            .map("k", "down_arrow")
        )
        alt = (
            LayerStackBuilder("alt", "right_option")
            .map("h", "home")
            .map("l", "end")
        )

        # Stacked layer
        hyper_alt = (
            LayerStackBuilder("hyper_alt", ["right_command", "right_option"])
            .map("i", "up_arrow")
            .map_macro("t", template_type="typed_text", text="Stacked!")
        )

        # Build profile
        profile = Profile("Multi-Layer Example")
        for layer in [hyper, alt, hyper_alt]:
            for rule in layer.build_rules():
                profile.add_rule(rule)

        config = KarabinerConfig().add_profile(profile)
        result = config.build()

        rules = result["profiles"][0]["complex_modifications"]["rules"]
        # hyper: 1 activation + 2 mappings = 3
        # alt: 1 activation + 2 mappings = 3
        # hyper_alt: 1 activation + 1 mapping + 1 macro = 3
        assert len(rules) == 9

    def test_save_and_load(self):
        """Test saving and loading configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.json"

            # Build and save
            hyper = LayerStackBuilder("hyper", "right_command").map("j", "left_arrow")
            profile = Profile("Test")
            for rule in hyper.build_rules():
                profile.add_rule(rule)

            config = KarabinerConfig().add_profile(profile)
            config.save(path=config_path)

            # Load and verify
            saved_data = json.loads(config_path.read_text())

            assert saved_data["global"]["check_for_updates_on_startup"] is True
            assert saved_data["profiles"][0]["name"] == "Test"
            assert len(saved_data["profiles"][0]["complex_modifications"]["rules"]) == 2

    def test_json_output_format(self):
        """Test that JSON output matches expected Karabiner format."""
        layer = LayerStackBuilder("hyper", "right_command").map("j", "left_arrow")
        profile = Profile("Test")
        for rule in layer.build_rules():
            profile.add_rule(rule)

        config = KarabinerConfig().add_profile(profile)
        json_str = config.to_json()
        data = json.loads(json_str)

        # Check activation rule structure
        activation = data["profiles"][0]["complex_modifications"]["rules"][0]
        assert activation["description"] == "hyper activation"
        assert activation["manipulators"][0]["from"]["key_code"] == "right_command"
        assert activation["manipulators"][0]["to"][0]["set_variable"]["name"] == "hyper"

        # Check mapping rule structure
        mapping = data["profiles"][0]["complex_modifications"]["rules"][1]
        assert "j → left_arrow" in mapping["description"]
        assert mapping["manipulators"][0]["conditions"][0]["type"] == "variable_if"

    def test_complex_layer_with_all_features(self):
        """Test a layer using all available features."""
        layer = (
            LayerStackBuilder("dev", "right_command")
            # Regular mappings
            .map("j", "left_arrow")
            .map("k", "down_arrow")
            .map("l", "right_arrow")
            .map("i", "up_arrow")
            # Combo
            .map_combo(["j", "k"], "escape")
            # Sequence
            .set_sequence_timeout(300)
            .map_sequence(["g", "g"], "home")
            # Macro
            .map_macro("t", template_type="typed_text", text="Dev mode!")
            # App condition
            .when_app(["com.apple.Terminal", "com.microsoft.VSCode"])
        )

        rules = layer.build_rules()

        # Verify all rule types are present
        descriptions = [r.build()["description"] for r in rules]

        assert any("activation" in d for d in descriptions)
        assert any("→ left_arrow" in d for d in descriptions)
        assert any("combo" in d for d in descriptions)
        assert any("sequence" in d for d in descriptions)
        assert any("macro" in d for d in descriptions)
