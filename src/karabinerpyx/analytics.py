"""Static analysis and coverage reporting for Karabiner configs."""

from __future__ import annotations

from typing import Any

from karabinerpyx.models import KarabinerConfig


def compute_static_coverage(config: KarabinerConfig) -> dict[str, Any]:
    """Compute static coverage and potential conflicts.

    Coverage here is a heuristic based on mapping uniqueness and overlap.
    """
    total_manipulators = 0
    from_signatures: dict[str, list[dict[str, Any]]] = {}

    for profile in config.profiles:
        for rule in profile.rules:
            for manip in rule.manipulators:
                total_manipulators += 1
                data = manip.build()
                signature = _from_signature(data)
                entry = {
                    "profile": profile.name,
                    "rule": rule.description,
                    "conditions": data.get("conditions", []),
                }
                from_signatures.setdefault(signature, []).append(entry)

    unique_from = len(from_signatures)
    duplicates = {k: v for k, v in from_signatures.items() if len(v) > 1}

    return {
        "total_manipulators": total_manipulators,
        "unique_from": unique_from,
        "duplicate_from": sum(len(v) - 1 for v in duplicates.values()),
        "potential_conflicts": duplicates,
    }


def format_coverage_report(report: dict[str, Any]) -> str:
    """Format coverage report as a human-readable string."""
    lines = [
        "Static Coverage Report",
        f"Total manipulators: {report['total_manipulators']}",
        f"Unique from signatures: {report['unique_from']}",
        f"Duplicate from signatures: {report['duplicate_from']}",
    ]

    conflicts = report["potential_conflicts"]
    if conflicts:
        lines.append("")
        lines.append("Potential conflicts (same from signature):")
        for signature, entries in conflicts.items():
            lines.append(f"- {signature}")
            for entry in entries:
                cond_summary = _format_condition_summary(entry["conditions"])
                lines.append(
                    f"  Profile: {entry['profile']} | Rule: {entry['rule']} | {cond_summary}"
                )

    return "\n".join(lines)


def _from_signature(manip: dict[str, Any]) -> str:
    from_block = manip.get("from", {})
    if "simultaneous" in from_block:
        keys = [
            entry.get("key_code", "unknown")
            for entry in from_block.get("simultaneous", [])
        ]
        return f"simultaneous({'+'.join(keys)})"
    key = from_block.get("key_code", "unknown")
    mods = from_block.get("modifiers", {})
    mandatory = mods.get("mandatory", [])
    optional = mods.get("optional", [])
    mod_part = ""
    if mandatory or optional:
        mod_part = f"|m:{'+'.join(sorted(mandatory))}|o:{'+'.join(sorted(optional))}"
    return f"key({key}){mod_part}"


def _format_condition_summary(conditions: list[dict[str, Any]]) -> str:
    if not conditions:
        return "Conditions: none"
    parts: list[str] = []
    for cond in conditions:
        cond_type = cond.get("type", "unknown")
        if cond_type == "frontmost_application_if":
            apps = ", ".join(cond.get("bundle_identifiers", []))
            parts.append(f"app_if({apps})")
        elif cond_type == "frontmost_application_unless":
            apps = ", ".join(cond.get("bundle_identifiers", []))
            parts.append(f"app_unless({apps})")
        elif cond_type in {"variable_if", "variable_unless"}:
            parts.append(f"{cond_type}({cond.get('name')}={cond.get('value')})")
        else:
            parts.append(cond_type)
    return f"Conditions: {'; '.join(parts)}"
