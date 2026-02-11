"""Static analysis and coverage reporting for Karabiner configs."""

from __future__ import annotations

import json
from typing import Any

from karabinerpyx.models import KarabinerConfig


def compute_static_coverage(config: KarabinerConfig) -> dict[str, Any]:
    """Compute static coverage and conflict heuristics."""
    total_manipulators = 0
    macro_mappings = 0

    from_groups: dict[str, list[dict[str, Any]]] = {}
    full_groups: dict[str, list[dict[str, Any]]] = {}

    for profile in config.profiles:
        for rule in profile.rules:
            for manipulator in rule.manipulators:
                total_manipulators += 1
                data = manipulator.build()

                if any("shell_command" in action for action in data.get("to", [])):
                    macro_mappings += 1

                from_signature = _from_signature(data)
                cond_signature = _condition_signature(data.get("conditions", []))
                full_signature = f"{from_signature}|conds:{cond_signature}"

                entry = {
                    "profile": profile.name,
                    "rule": rule.description,
                    "conditions": data.get("conditions", []),
                    "from_signature": from_signature,
                    "condition_signature": cond_signature,
                }
                from_groups.setdefault(from_signature, []).append(entry)
                full_groups.setdefault(full_signature, []).append(entry)

    unique_from = len(from_groups)
    duplicate_from = sum(
        len(entries) - 1 for entries in from_groups.values() if len(entries) > 1
    )

    potential_conflicts = {
        signature: entries
        for signature, entries in from_groups.items()
        if len(entries) > 1
    }

    branching_groups = sum(
        1
        for entries in from_groups.values()
        if len({entry["condition_signature"] for entry in entries}) > 1
    )

    unreachable_rules: list[dict[str, Any]] = []
    for entries in full_groups.values():
        if len(entries) > 1:
            unreachable_rules.extend(entries[1:])

    conflict_rate = duplicate_from / total_manipulators if total_manipulators else 0.0
    condition_branching_rate = branching_groups / unique_from if unique_from else 0.0
    macro_ratio = macro_mappings / total_manipulators if total_manipulators else 0.0

    return {
        "total_manipulators": total_manipulators,
        "unique_from": unique_from,
        "duplicate_from": duplicate_from,
        "conflict_rate": round(conflict_rate, 4),
        "condition_branching_rate": round(condition_branching_rate, 4),
        "macro_ratio": round(macro_ratio, 4),
        "potential_conflicts": potential_conflicts,
        "unreachable_rules": unreachable_rules,
    }


def format_coverage_report(report: dict[str, Any]) -> str:
    """Format coverage report as human-readable text."""
    lines = [
        "Static Coverage Report",
        f"Total manipulators: {report['total_manipulators']}",
        f"Unique from signatures: {report['unique_from']}",
        f"Duplicate from signatures: {report['duplicate_from']}",
        f"Conflict rate: {report['conflict_rate']:.2%}",
        f"Condition branching rate: {report['condition_branching_rate']:.2%}",
        f"Macro ratio: {report['macro_ratio']:.2%}",
        f"Potentially unreachable mappings: {len(report['unreachable_rules'])}",
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
                    "  Profile: "
                    f"{entry['profile']} | Rule: {entry['rule']} | {cond_summary}"
                )

    return "\n".join(lines)


def _from_signature(manip: dict[str, Any]) -> str:
    from_block = manip.get("from", {})
    if "simultaneous" in from_block:
        keys = [
            entry.get("key_code", "unknown")
            for entry in from_block.get("simultaneous", [])
        ]
        options = from_block.get("simultaneous_options", {})
        option_part = ""
        if options:
            option_part = (
                f"|opts:{json.dumps(options, sort_keys=True, separators=(',', ':'))}"
            )
        return f"simultaneous({'+'.join(keys)}){option_part}"

    key = from_block.get("key_code", "unknown")
    mods = from_block.get("modifiers", {})
    mandatory = mods.get("mandatory", [])
    optional = mods.get("optional", [])
    mod_part = ""
    if mandatory or optional:
        mandatory_part = "+".join(sorted(mandatory))
        optional_part = "+".join(sorted(optional))
        mod_part = f"|m:{mandatory_part}|o:{optional_part}"
    return f"key({key}){mod_part}"


def _condition_signature(conditions: list[dict[str, Any]]) -> str:
    if not conditions:
        return "none"
    normalized = [
        json.dumps(cond, sort_keys=True, separators=(",", ":")) for cond in conditions
    ]
    return "|".join(sorted(normalized))


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
            parts.append(str(cond_type))
    return f"Conditions: {'; '.join(parts)}"
