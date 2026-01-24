from __future__ import annotations

from typing import TYPE_CHECKING
from pathlib import Path

if TYPE_CHECKING:
    from karabinerpyx.models import KarabinerConfig


def generate_markdown(config: KarabinerConfig) -> str:
    """Generate a Markdown cheat sheet from the configuration."""
    lines = ["# ⌨️ KarabinerPyX Mapping Cheat Sheet", ""]

    for profile in config.profiles:
        lines.append(f"## 👤 Profile: {profile.name}")
        if profile.selected:
            lines[-1] += " (Selected)"
        lines.append("")

        for rule in profile.rules:
            lines.append(f"### 📜 {rule.description}")
            lines.append("")
            lines.append("| From | To | Conditions |")
            lines.append("| :--- | :--- | :--- |")

            for manip in rule.manipulators:
                # Basic manipulator representation
                # This could be improved by checking specific types of manipulators
                from_str = f"`{manip.from_key}`"
                
                to_parts = []
                if manip.to_keys:
                    to_parts.append(f"→ `{' + '.join(manip.to_keys)}`")
                if manip.to_if_alone:
                    to_parts.append(f"Alone: `{' + '.join(manip.to_if_alone)}`")
                if manip.to_if_held_down:
                    to_parts.append(f"Held: `{' + '.join(manip.to_if_held_down)}`")
                
                to_str = "<br>".join(to_parts)
                
                cond_parts = []
                for cond in manip.conditions:
                    if cond["type"] == "frontmost_application_if":
                        apps = ", ".join(cond["bundle_identifiers"])
                        cond_parts.append(f"App: {apps}")
                    elif cond["type"] == "variable_if":
                        cond_parts.append(f"Var: {cond['name']}=={cond['value']}")
                    else:
                        cond_parts.append(cond["type"])
                
                cond_str = "<br>".join(cond_parts) if cond_parts else "-"
                
                lines.append(f"| {from_str} | {to_str} | {cond_str} |")
            
            lines.append("")
    
    return "\n".join(lines)


def save_cheat_sheet(config: KarabinerConfig, path: Path | str) -> Path:
    """Generate and save the cheat sheet to a file."""
    md = generate_markdown(config)
    output_path = Path(path)
    output_path.write_text(md)
    print(f"📖 Cheat sheet generated at {output_path}")
    return output_path
