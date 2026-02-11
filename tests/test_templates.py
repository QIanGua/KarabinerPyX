"""Tests for template system."""

import pytest

from karabinerpyx import MACRO_TEMPLATES, make_shell_command
from karabinerpyx.templates import register_template


class TestMacroTemplates:
    """Tests for MACRO_TEMPLATES."""

    def test_typed_text_template_exists(self):
        """Test typed_text template is defined."""
        assert "typed_text" in MACRO_TEMPLATES

    def test_alfred_template_exists(self):
        """Test alfred template is defined."""
        assert "alfred" in MACRO_TEMPLATES

    def test_keyboard_maestro_template_exists(self):
        """Test keyboard_maestro template is defined."""
        assert "keyboard_maestro" in MACRO_TEMPLATES

    def test_open_template_exists(self):
        """Test open template is defined."""
        assert "open" in MACRO_TEMPLATES


class TestMakeShellCommand:
    """Tests for make_shell_command function."""

    def test_typed_text(self):
        """Test typed_text template."""
        result = make_shell_command("typed_text", text="Hello, world!")

        assert len(result) == 1
        assert "shell_command" in result[0]
        assert "Hello, world!" in result[0]["shell_command"]
        assert "System Events" in result[0]["shell_command"]

    def test_alfred(self):
        """Test alfred template."""
        result = make_shell_command(
            "alfred",
            trigger="search",
            workflow="MyWorkflow",
            arg="query",
        )

        assert "search" in result[0]["shell_command"]
        assert "MyWorkflow" in result[0]["shell_command"]
        assert "query" in result[0]["shell_command"]

    def test_keyboard_maestro(self):
        """Test keyboard_maestro template."""
        result = make_shell_command("keyboard_maestro", script="MyMacro")

        assert "MyMacro" in result[0]["shell_command"]
        assert "Keyboard Maestro Engine" in result[0]["shell_command"]

    def test_open(self):
        """Test open template."""
        result = make_shell_command("open", path="/Applications/Safari.app")

        assert result[0]["shell_command"] == 'open "/Applications/Safari.app"'

    def test_unknown_template_raises(self):
        """Test that unknown template raises ValueError."""
        with pytest.raises(ValueError, match="Unknown template"):
            make_shell_command("nonexistent_template")

    def test_missing_template_param_raises(self):
        """Test that missing template params raise ValueError."""
        with pytest.raises(ValueError, match="Missing template parameter"):
            make_shell_command("typed_text")


class TestRegisterTemplate:
    """Tests for register_template function."""

    def test_register_custom_template(self):
        """Test registering a custom template."""
        register_template("my_custom", 'echo "{message}"')

        assert "my_custom" in MACRO_TEMPLATES
        result = make_shell_command("my_custom", message="hello")
        assert result[0]["shell_command"] == 'echo "hello"'

    def test_register_invalid_template_inputs(self):
        """Test validation for template registration."""
        with pytest.raises(ValueError, match="Template name cannot be empty"):
            register_template("", "echo 1")

        with pytest.raises(ValueError, match="Template cannot be empty"):
            register_template("x", "")
