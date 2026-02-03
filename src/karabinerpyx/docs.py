from __future__ import annotations

from typing import TYPE_CHECKING, Any
from pathlib import Path

if TYPE_CHECKING:
    from karabinerpyx.models import KarabinerConfig


def generate_markdown(config: KarabinerConfig) -> str:
    """Generate a Markdown cheat sheet from the configuration."""
    lines = ["# KarabinerPyX Mapping Cheat Sheet", ""]

    for profile in config.profiles:
        lines.append(f"## Profile: {profile.name}")
        if profile.selected:
            lines[-1] += " (Selected)"
        lines.append("")

        for rule in profile.rules:
            lines.append(f"### {rule.description}")
            lines.append("")
            lines.append("| From | To | Conditions |")
            lines.append("| :--- | :--- | :--- |")

            for manip in rule.manipulators:
                data = manip.build()
                from_str = _format_from(data)
                to_str = _format_to(data)
                cond_str = _format_conditions(data)

                lines.append(f"| {from_str} | {to_str} | {cond_str} |")

            lines.append("")

    return "\n".join(lines)


def generate_html(config: KarabinerConfig) -> str:
    """Generate an HTML cheat sheet from the configuration."""
    sections: list[str] = [
        "<!doctype html>",
        "<html lang=\"en\">",
        "<head>",
        "<meta charset=\"utf-8\" />",
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />",
        "<title>KarabinerPyX Mapping Cheat Sheet</title>",
        "<style>",
        ":root {",
        "  --ink: #1b2a34;",
        "  --muted: #51606a;",
        "  --card: #ffffff;",
        "  --border: #d6dee6;",
        "  --accent: #1f6f8b;",
        "  --accent-2: #e6f1f5;",
        "  --shadow: 0 12px 32px rgba(31, 42, 52, 0.12);",
        "}",
        "body {",
        "  font-family: \"Iowan Old Style\", \"Charter\", \"Palatino\", serif;",
        "  margin: 0;",
        "  color: var(--ink);",
        "  background: radial-gradient(circle at top, #eef6f9, #f7fbfd 60%, #ffffff);",
        "}",
        ".page { max-width: 980px; margin: 0 auto; padding: 36px 28px 60px; }",
        "header {",
        "  background: linear-gradient(135deg, #e9f3f7, #ffffff 60%);",
        "  border: 1px solid var(--border);",
        "  border-radius: 16px;",
        "  padding: 24px 26px;",
        "  box-shadow: var(--shadow);",
        "}",
        "h1 { font-size: 30px; margin: 0 0 6px; letter-spacing: 0.3px; }",
        "header p { margin: 0; color: var(--muted); }",
        "h2 { font-size: 20px; margin: 32px 0 8px; }",
        "h3 { font-size: 16px; margin: 18px 0 6px; color: var(--accent); }",
        ".profile { margin-top: 26px; }",
        ".rule {",
        "  background: var(--card);",
        "  border: 1px solid var(--border);",
        "  border-radius: 14px;",
        "  padding: 14px 16px;",
        "  margin-bottom: 16px;",
        "  box-shadow: 0 8px 22px rgba(31, 42, 52, 0.08);",
        "}",
        "table { width: 100%; border-collapse: collapse; margin: 8px 0 0; }",
        "th, td { border-bottom: 1px solid var(--border); padding: 8px 10px; text-align: left; }",
        "th { background: var(--accent-2); font-weight: 600; }",
        "tr:last-child td { border-bottom: none; }",
        "code {",
        "  background: #f1f5f7;",
        "  padding: 2px 6px;",
        "  border-radius: 6px;",
        "  font-family: \"SF Mono\", \"Fira Code\", \"Source Code Pro\", monospace;",
        "  font-size: 13px;",
        "}",
        ".conditions { color: var(--muted); font-size: 13px; }",
        ".to-cell code { background: #eef3f7; }",
        "</style>",
        "</head>",
        "<body>",
        "<div class=\"page\">",
        "<header>",
        "<h1>KarabinerPyX Mapping Cheat Sheet</h1>",
        "<p>Auto-generated reference of your custom layers, combos, and rules.</p>",
        "</header>",
    ]

    for profile in config.profiles:
        profile_title = f"Profile: {profile.name}"
        if profile.selected:
            profile_title += " (Selected)"
        sections.append(f"<div class=\"profile\"><h2>{profile_title}</h2>")

        for rule in profile.rules:
            sections.append("<div class=\"rule\">")
            sections.append(f"<h3>{rule.description}</h3>")
            sections.append("<table>")
            sections.append("<thead><tr><th>From</th><th>To</th><th>Conditions</th></tr></thead>")
            sections.append("<tbody>")

            for manip in rule.manipulators:
                data = manip.build()
                from_str = _format_from(data).strip("`")
                to_str = _format_to(data).replace("`", "")
                cond_str = _format_conditions(data)
                cond_cell = cond_str if cond_str != "-" else ""
                sections.append(
                    "<tr>"
                    f"<td><code>{from_str}</code></td>"
                    f"<td class=\"to-cell\">{to_str}</td>"
                    f"<td class=\"conditions\">{cond_cell}</td>"
                    "</tr>"
                )

            sections.append("</tbody></table></div>")

        sections.append("</div>")

    sections.append("</div></body></html>")
    return "\n".join(sections)


def save_cheat_sheet(config: KarabinerConfig, path: Path | str) -> Path:
    """Generate and save the cheat sheet to a file."""
    md = generate_markdown(config)
    output_path = Path(path)
    output_path.write_text(md)
    print(f"Cheat sheet generated at {output_path}")
    return output_path


def save_cheat_sheet_html(config: KarabinerConfig, path: Path | str) -> Path:
    """Generate and save the HTML cheat sheet to a file."""
    html = generate_html(config)
    output_path = Path(path)
    output_path.write_text(html)
    print(f"HTML cheat sheet generated at {output_path}")
    return output_path


def _format_from(manip: dict[str, Any]) -> str:
    from_block = manip.get("from", {})
    if "simultaneous" in from_block:
        keys = [
            entry.get("key_code", "unknown")
            for entry in from_block.get("simultaneous", [])
        ]
        return f"`{' + '.join(keys)}`"
    if "key_code" in from_block:
        return f"`{from_block['key_code']}`"
    return "`unknown`"


def _format_action(action: dict[str, Any]) -> str:
    if "key_code" in action:
        return action["key_code"]
    if "set_variable" in action:
        details = action["set_variable"]
        return f"set_variable({details.get('name')}={details.get('value')})"
    if "shell_command" in action:
        return "shell_command"
    return "unknown"


def _format_to(manip: dict[str, Any]) -> str:
    to_parts: list[str] = []

    def format_actions(label: str, actions: list[dict[str, Any]]) -> None:
        keys = [_format_action(action) for action in actions]
        if keys:
            to_parts.append(f"{label}`{' + '.join(keys)}`")

    format_actions("→ ", manip.get("to", []))
    format_actions("Alone: ", manip.get("to_if_alone", []))
    format_actions("Held: ", manip.get("to_if_held_down", []))

    return "<br>".join(to_parts) if to_parts else "-"


def _format_conditions(manip: dict[str, Any]) -> str:
    cond_parts: list[str] = []
    for cond in manip.get("conditions", []):
        if cond["type"] == "frontmost_application_if":
            apps = ", ".join(cond["bundle_identifiers"])
            cond_parts.append(f"App: {apps}")
        elif cond["type"] == "variable_if":
            cond_parts.append(f"Var: {cond['name']}=={cond['value']}")
        else:
            cond_parts.append(cond["type"])

    return "<br>".join(cond_parts) if cond_parts else "-"
