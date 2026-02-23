"""Compiler from intent DSL to low-level Karabiner models."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from karabinerpyx.layer import LayerStackBuilder
from karabinerpyx.models import KarabinerConfig, Manipulator, Profile, Rule

if TYPE_CHECKING:
    from karabinerpyx.intent import IntentConfig, IntentLayer, IntentProfile


def compile_intent(config: IntentConfig) -> KarabinerConfig:
    """Compile intent config into low-level KarabinerConfig."""
    result = KarabinerConfig()

    for intent_profile in config.profiles:
        profile = Profile(intent_profile.name, selected=intent_profile.selected)

        for rule in _compile_dual_roles(intent_profile):
            profile.add_rule(rule)

        for rule in _compile_profile_mappings(intent_profile):
            profile.add_rule(rule)

        for layer in intent_profile.layers:
            for rule in _compile_layer(intent_profile.name, layer):
                profile.add_rule(rule)

        for description, manipulator in intent_profile.raw_manipulators:
            profile.add_rule(Rule(description).add_raw(manipulator))

        result.add_profile(profile)

    return result


def _compile_dual_roles(profile: IntentProfile) -> list[Rule]:
    rules: list[Rule] = []
    for key, tap, hold in profile.dual_roles:
        rule = Rule(f"Dual role: {key} tap {tap}, hold {hold}")
        manip = Manipulator(key).to(hold).if_alone(tap)
        rules.append(rule.add(manip))
    return rules


def _compile_profile_mappings(profile: IntentProfile) -> list[Rule]:
    rules: list[Rule] = []
    for from_key, to_target in profile.mappings:
        rule = Rule(f"Profile: {from_key} -> {to_target}")
        manip = Manipulator(from_key).modifiers(optional=["any"])
        if isinstance(to_target, dict):
            manip.to_raw(to_target)
        else:
            manip.to(to_target)
        rules.append(rule.add(manip))
    return rules


def _compile_layer(profile_name: str, layer: IntentLayer) -> list[Rule]:
    builder = LayerStackBuilder(
        layer.name,
        layer.trigger_keys,
        to_if_alone=layer.to_if_alone,
    )

    for apps in layer.app_conditions_if:
        builder.when_app(apps)
    for apps in layer.app_conditions_unless:
        builder.unless_app(apps)

    rules: list[Rule] = []

    # Compile order is fixed for deterministic output and tests.
    rules.append(builder._build_activation_rule())

    if layer.mappings:
        builder.mappings = list(layer.mappings)
        rules.extend(builder._build_mapping_rules())

    if layer.combos:
        builder.combos = list(layer.combos)
        rules.extend(builder._build_combo_rules())

    if layer.sequences:
        sequence_prefix = _build_sequence_prefix(profile_name, layer.name)
        for keys, to_key, timeout_ms in layer.sequences:
            builder.sequences = [(keys, to_key)]
            builder.set_sequence_timeout(timeout_ms)
            builder.set_sequence_variable_prefix(sequence_prefix)
            rules.extend(builder._build_sequence_rules())
        builder.set_sequence_variable_prefix(None)

    if layer.macros:
        builder.mappings = [
            (from_key, {"template": template, "params": params})
            for from_key, template, params in layer.macros
        ]
        rules.extend(builder._build_mapping_rules())

    for description, manipulator in layer.raw_manipulators:
        rules.append(Rule(description).add_raw(manipulator))

    return rules


def _build_sequence_prefix(profile_name: str, layer_name: str) -> str:
    profile_component = _sanitize_component(profile_name)
    layer_component = _sanitize_component(layer_name)
    return f"__kpyx_seq_{profile_component}_{layer_component}"


def _sanitize_component(value: str) -> str:
    sanitized = re.sub(r"[^0-9A-Za-z]+", "_", value).strip("_").lower()
    return sanitized or "default"
