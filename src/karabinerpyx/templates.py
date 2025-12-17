"""Macro templates for shell commands."""

from __future__ import annotations

from typing import Any

# Predefined macro templates
MACRO_TEMPLATES: dict[str, str] = {
    "typed_text": (
        'osascript -e \'tell application "System Events" to keystroke "{text}"\''
    ),
    "alfred": (
        'osascript -e \'tell application id "com.runningwithcrayons.Alfred" '
        'to run trigger "{trigger}" in workflow "{workflow}" with argument "{arg}"\''
    ),
    "keyboard_maestro": (
        'osascript -e \'tell application "Keyboard Maestro Engine" '
        'to do script "{script}"\''
    ),
    "open": 'open "{path}"',
    "shell": "{command}",
}


def make_shell_command(
    template_name: str,
    **kwargs: Any,
) -> list[dict[str, str]]:
    """Generate a shell command from a template.

    Args:
        template_name: Name of the template to use.
        **kwargs: Parameters to fill into the template.

    Returns:
        A list containing the shell_command dict.

    Raises:
        ValueError: If template_name is not found.
    """
    template = MACRO_TEMPLATES.get(template_name)
    if not template:
        raise ValueError(f"Unknown template: {template_name}")
    return [{"shell_command": template.format(**kwargs)}]


def register_template(name: str, template: str) -> None:
    """Register a custom template.

    Args:
        name: Template name.
        template: Template string with {placeholders}.
    """
    MACRO_TEMPLATES[name] = template
