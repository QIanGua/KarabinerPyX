"""Macro templates for shell commands."""

from __future__ import annotations

from typing import Any

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


def make_shell_command(template_name: str, **kwargs: Any) -> list[dict[str, str]]:
    """Generate a shell command action list from template name and params."""
    template = MACRO_TEMPLATES.get(template_name)
    if template is None:
        raise ValueError(f"Unknown template: {template_name}")

    try:
        command = template.format(**kwargs)
    except KeyError as exc:
        missing = exc.args[0]
        raise ValueError(
            f"Missing template parameter '{missing}' for template '{template_name}'"
        ) from exc

    return [{"shell_command": command}]


def register_template(name: str, template: str) -> None:
    """Register a custom template."""
    if not name:
        raise ValueError("Template name cannot be empty")
    if not template:
        raise ValueError("Template cannot be empty")
    MACRO_TEMPLATES[name] = template
