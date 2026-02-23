"""Semantic linting for intent and low-level Karabiner configurations."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any, Literal

from karabinerpyx.analytics import compute_static_coverage
from karabinerpyx.compiler import compile_intent
from karabinerpyx.models import KarabinerConfig
from karabinerpyx.templates import make_shell_command

if TYPE_CHECKING:
    from karabinerpyx.intent import IntentConfig


@dataclass(frozen=True)
class LintIssue:
    """A lint finding with severity and source location."""

    code: str
    message: str
    severity: Literal["error", "warning"]
    profile: str | None = None
    rule: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert lint issue into JSON-serializable dictionary."""
        return asdict(self)


def lint_intent(config: IntentConfig) -> list[LintIssue]:
    """Lint an intent config for semantic and compilation issues."""
    issues: list[LintIssue] = []

    for profile in config.profiles:
        for layer in profile.layers:
            if not layer.trigger_keys:
                issues.append(
                    LintIssue(
                        code="empty_trigger",
                        message=f"Layer '{layer.name}' has no trigger keys.",
                        severity="error",
                        profile=profile.name,
                        rule=layer.name,
                    )
                )
            for from_key, template, params in layer.macros:
                try:
                    make_shell_command(template, **params)
                except ValueError as exc:
                    detail = f"'{from_key}' in layer '{layer.name}' is invalid: {exc}"
                    issues.append(
                        LintIssue(
                            code="invalid_macro",
                            message=f"Macro {detail}",
                            severity="error",
                            profile=profile.name,
                            rule=layer.name,
                        )
                    )

    try:
        compiled = compile_intent(config)
    except ValueError as exc:
        issues.append(
            LintIssue(
                code="compile_error",
                message=f"Intent compilation failed: {exc}",
                severity="error",
            )
        )
        return issues

    issues.extend(lint_karabiner_config(compiled, allow_shadow=config.allow_shadow))
    return issues


def lint_karabiner_config(
    config: KarabinerConfig,
    allow_shadow: bool = False,
) -> list[LintIssue]:
    """Lint a low-level config for conflicts and unreachable mappings."""
    issues: list[LintIssue] = []

    signatures: dict[str, list[tuple[str, str]]] = {}
    for profile_name, rule_description, manip in _iter_manipulators(config):
        condition_part = _condition_signature(manip.get("conditions", []))
        signature = (
            f"{_from_signature(manip)}|conds:{condition_part}"
        )
        signatures.setdefault(signature, []).append((profile_name, rule_description))

    for signature, locations in signatures.items():
        if len(locations) <= 1:
            continue

        first_profile, first_rule = locations[0]
        duplicate_count = len(locations) - 1

        if allow_shadow:
            issues.append(
                LintIssue(
                    code="shadowed_mapping",
                    message=(
                        "Mapping signature appears multiple times "
                        f"({duplicate_count} shadowed): {signature}"
                    ),
                    severity="warning",
                    profile=first_profile,
                    rule=first_rule,
                )
            )
        else:
            issues.append(
                LintIssue(
                    code="duplicate_mapping",
                    message=(
                        "Duplicate mapping signature detected "
                        f"({duplicate_count} duplicates): {signature}"
                    ),
                    severity="error",
                    profile=first_profile,
                    rule=first_rule,
                )
            )

        for duplicate_profile, duplicate_rule in locations[1:]:
            issues.append(
                LintIssue(
                    code="unreachable_mapping",
                    message=f"Rule is shadowed by a prior mapping: {signature}",
                    severity="warning",
                    profile=duplicate_profile,
                    rule=duplicate_rule,
                )
            )

    report = compute_static_coverage(config)
    if report["potential_conflicts"]:
        issues.append(
            LintIssue(
                code="potential_conflict",
                message=(
                    "Mappings share the same from-signature with different conditions: "
                    f"{len(report['potential_conflicts'])} groups"
                ),
                severity="warning",
            )
        )

    return issues


def _iter_manipulators(
    config: KarabinerConfig,
) -> list[tuple[str, str, dict[str, Any]]]:
    rows: list[tuple[str, str, dict[str, Any]]] = []
    for profile in config.profiles:
        for rule in profile.rules:
            for manipulator in rule.manipulators:
                rows.append((profile.name, rule.description, manipulator.build()))
    return rows


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
        json.dumps(condition, sort_keys=True, separators=(",", ":"))
        for condition in conditions
    ]
    return "|".join(sorted(normalized))
