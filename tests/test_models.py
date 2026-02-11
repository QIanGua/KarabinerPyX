"""Tests for core models."""

from __future__ import annotations

import warnings

from karabinerpyx import KarabinerConfig, Manipulator, Profile, RawManipulator, Rule


class TestManipulator:
    def test_simple_mapping(self):
        manipulator = Manipulator("a").to("b")
        result = manipulator.build()

        assert result["type"] == "basic"
        assert result["from"]["key_code"] == "a"
        assert result["to"] == [{"key_code": "b"}]

    def test_multiple_to_keys(self):
        manipulator = Manipulator("a").to("b").to("c")
        result = manipulator.build()

        assert result["to"] == [{"key_code": "b"}, {"key_code": "c"}]

    def test_if_alone(self):
        manipulator = Manipulator("caps_lock").if_alone("escape")
        result = manipulator.build()

        assert result["to_if_alone"] == [{"key_code": "escape"}]

    def test_if_held(self):
        manipulator = Manipulator("caps_lock").if_held("left_control")
        result = manipulator.build()

        assert result["to_if_held_down"] == [{"key_code": "left_control"}]

    def test_when_app_single(self):
        manipulator = Manipulator("a").to("b").when_app("com.apple.Terminal")
        result = manipulator.build()

        assert len(result["conditions"]) == 1
        assert result["conditions"][0]["type"] == "frontmost_application_if"
        assert result["conditions"][0]["bundle_identifiers"] == ["com.apple.Terminal"]

    def test_when_app_multiple(self):
        manipulator = (
            Manipulator("a")
            .to("b")
            .when_app(["com.apple.Terminal", "com.microsoft.VSCode"])
        )
        result = manipulator.build()

        assert result["conditions"][0]["bundle_identifiers"] == [
            "com.apple.Terminal",
            "com.microsoft.VSCode",
        ]

    def test_when_variable(self):
        manipulator = Manipulator("a").to("b").when_variable("hyper", 1)
        result = manipulator.build()

        assert result["conditions"][0] == {
            "type": "variable_if",
            "name": "hyper",
            "value": 1,
        }

    def test_chaining(self):
        manipulator = (
            Manipulator("caps_lock")
            .to("left_control")
            .if_alone("escape")
            .when_app("com.apple.Terminal")
        )
        result = manipulator.build()

        assert result["to"] == [{"key_code": "left_control"}]
        assert result["to_if_alone"] == [{"key_code": "escape"}]
        assert len(result["conditions"]) == 1


class TestRule:
    def test_basic_rule(self):
        rule = Rule("Test mapping").add(Manipulator("a").to("b"))
        result = rule.build()

        assert result["description"] == "Test mapping"
        assert len(result["manipulators"]) == 1

    def test_multiple_manipulators(self):
        rule = Rule("Multiple mappings")
        rule.add(Manipulator("a").to("b"))
        rule.add(Manipulator("c").to("d"))
        result = rule.build()

        assert len(result["manipulators"]) == 2

    def test_extend(self):
        rule = Rule("Extended rule").extend(
            [
                Manipulator("a").to("b"),
                Manipulator("c").to("d"),
            ]
        )
        result = rule.build()

        assert len(result["manipulators"]) == 2

    def test_add_raw(self):
        raw = {
            "type": "basic",
            "from": {"key_code": "a"},
            "to": [{"key_code": "b"}],
        }
        rule = Rule("Raw mapping").add_raw(raw)
        result = rule.build()

        assert result["manipulators"][0] == raw

    def test_add_dict_deprecated(self):
        raw = {
            "type": "basic",
            "from": {"key_code": "a"},
            "to": [{"key_code": "b"}],
        }

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            rule = Rule("Raw mapping").add_dict(raw)
            result = rule.build()

        assert result["manipulators"][0] == raw
        assert any(item.category is DeprecationWarning for item in caught)

    def test_raw_manipulator_validation(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            RawManipulator({"from": {"key_code": "a"}, "type": "basic"})


class TestProfile:
    def test_basic_profile(self):
        profile = Profile("My Profile")
        profile.add_rule(Rule("Test").add(Manipulator("a").to("b")))
        result = profile.build()

        assert result["name"] == "My Profile"
        assert result["selected"] is True
        assert "complex_modifications" in result
        assert len(result["complex_modifications"]["rules"]) == 1

    def test_unselected_profile(self):
        profile = Profile("Inactive", selected=False)
        result = profile.build()

        assert result["selected"] is False


class TestKarabinerConfig:
    def test_basic_config(self, simple_profile):
        config = KarabinerConfig().add_profile(simple_profile)
        result = config.build()

        assert "global" in result
        assert "profiles" in result
        assert len(result["profiles"]) == 1

    def test_global_settings(self):
        config = KarabinerConfig()
        result = config.build()

        assert result["global"]["check_for_updates_on_startup"] is True
        assert result["global"]["show_in_menu_bar"] is True

    def test_to_json(self, simple_config):
        json_str = simple_config.to_json()

        assert '"global"' in json_str
        assert '"profiles"' in json_str

    def test_multiple_profiles(self):
        config = KarabinerConfig()
        config.add_profile(Profile("Profile 1"))
        config.add_profile(Profile("Profile 2", selected=False))
        result = config.build()

        assert len(result["profiles"]) == 2
