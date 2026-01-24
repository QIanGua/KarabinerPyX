"""Tests for core models."""

from karabinerpyx import KarabinerConfig, Manipulator, Profile, Rule


class TestManipulator:
    """Tests for Manipulator class."""

    def test_simple_mapping(self):
        """Test simple key mapping."""
        m = Manipulator("a").to("b")
        result = m.build()

        assert result["type"] == "basic"
        assert result["from"]["key_code"] == "a"
        assert result["to"] == [{"key_code": "b"}]

    def test_multiple_to_keys(self):
        """Test mapping to multiple keys."""
        m = Manipulator("a").to("b").to("c")
        result = m.build()

        assert result["to"] == [{"key_code": "b"}, {"key_code": "c"}]

    def test_if_alone(self):
        """Test to_if_alone behavior."""
        m = Manipulator("caps_lock").if_alone("escape")
        result = m.build()

        assert result["to_if_alone"] == [{"key_code": "escape"}]

    def test_if_held(self):
        """Test to_if_held_down behavior."""
        m = Manipulator("caps_lock").if_held("left_control")
        result = m.build()

        assert result["to_if_held_down"] == [{"key_code": "left_control"}]

    def test_when_app_single(self):
        """Test single app condition."""
        m = Manipulator("a").to("b").when_app("com.apple.Terminal")
        result = m.build()

        assert len(result["conditions"]) == 1
        assert result["conditions"][0]["type"] == "frontmost_application_if"
        assert result["conditions"][0]["bundle_identifiers"] == ["com.apple.Terminal"]

    def test_when_app_multiple(self):
        """Test multiple app conditions."""
        m = (
            Manipulator("a")
            .to("b")
            .when_app(["com.apple.Terminal", "com.microsoft.VSCode"])
        )
        result = m.build()

        assert result["conditions"][0]["bundle_identifiers"] == [
            "com.apple.Terminal",
            "com.microsoft.VSCode",
        ]

    def test_when_variable(self):
        """Test variable condition."""
        m = Manipulator("a").to("b").when_variable("hyper", 1)
        result = m.build()

        assert result["conditions"][0] == {
            "type": "variable_if",
            "name": "hyper",
            "value": 1,
        }

    def test_chaining(self):
        """Test fluent API chaining."""
        m = (
            Manipulator("caps_lock")
            .to("left_control")
            .if_alone("escape")
            .when_app("com.apple.Terminal")
        )
        result = m.build()

        assert result["to"] == [{"key_code": "left_control"}]
        assert result["to_if_alone"] == [{"key_code": "escape"}]
        assert len(result["conditions"]) == 1


class TestRule:
    """Tests for Rule class."""

    def test_basic_rule(self):
        """Test basic rule building."""
        rule = Rule("Test mapping").add(Manipulator("a").to("b"))
        result = rule.build()

        assert result["description"] == "Test mapping"
        assert len(result["manipulators"]) == 1

    def test_multiple_manipulators(self):
        """Test rule with multiple manipulators."""
        rule = Rule("Multiple mappings")
        rule.add(Manipulator("a").to("b"))
        rule.add(Manipulator("c").to("d"))
        result = rule.build()

        assert len(result["manipulators"]) == 2

    def test_extend(self):
        """Test extending rule with multiple manipulators."""
        rule = Rule("Extended rule").extend(
            [
                Manipulator("a").to("b"),
                Manipulator("c").to("d"),
            ]
        )
        result = rule.build()

        assert len(result["manipulators"]) == 2

    def test_add_dict(self):
        """Test adding raw manipulator dict."""
        raw = {
            "type": "basic",
            "from": {"key_code": "a"},
            "to": [{"key_code": "b"}],
        }
        rule = Rule("Raw mapping").add_dict(raw)
        result = rule.build()

        assert result["manipulators"][0] == raw


class TestProfile:
    """Tests for Profile class."""

    def test_basic_profile(self):
        """Test basic profile building."""
        profile = Profile("My Profile")
        profile.add_rule(Rule("Test").add(Manipulator("a").to("b")))
        result = profile.build()

        assert result["name"] == "My Profile"
        assert result["selected"] is True
        assert "complex_modifications" in result
        assert len(result["complex_modifications"]["rules"]) == 1

    def test_unselected_profile(self):
        """Test unselected profile."""
        profile = Profile("Inactive", selected=False)
        result = profile.build()

        assert result["selected"] is False


class TestKarabinerConfig:
    """Tests for KarabinerConfig class."""

    def test_basic_config(self, simple_profile):
        """Test basic config building."""
        config = KarabinerConfig().add_profile(simple_profile)
        result = config.build()

        assert "global" in result
        assert "profiles" in result
        assert len(result["profiles"]) == 1

    def test_global_settings(self):
        """Test global settings."""
        config = KarabinerConfig()
        result = config.build()

        assert result["global"]["check_for_updates_on_startup"] is True
        assert result["global"]["show_in_menu_bar"] is True

    def test_to_json(self, simple_config):
        """Test JSON generation."""
        json_str = simple_config.to_json()

        assert '"global"' in json_str
        assert '"profiles"' in json_str

    def test_multiple_profiles(self):
        """Test multiple profiles."""
        config = KarabinerConfig()
        config.add_profile(Profile("Profile 1"))
        config.add_profile(Profile("Profile 2", selected=False))
        result = config.build()

        assert len(result["profiles"]) == 2
