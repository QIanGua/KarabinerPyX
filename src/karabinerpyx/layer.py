"""Layer DSL and higher-level manipulators."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from karabinerpyx.models import RawManipulator, Rule
from karabinerpyx.templates import make_shell_command


@dataclass
class SimultaneousManipulator:
    """Manipulator for simultaneous key presses."""

    combo_keys: list[str]
    to_target: list[dict[str, Any]]
    variable_name: str
    extra_conditions: list[dict[str, Any]]
    options: dict[str, Any]

    def __init__(
        self,
        combo_keys: list[str],
        to_key: str | list[dict[str, Any]],
        variable_name: str,
        conditions: list[dict[str, Any]] | None = None,
        **options: Any,
    ):
        if len(combo_keys) < 2:
            raise ValueError("combo_keys must contain at least two keys")
        if any(not key for key in combo_keys):
            raise ValueError("combo_keys cannot contain empty keys")
        self.combo_keys = combo_keys
        self.to_target = to_key if isinstance(to_key, list) else [{"key_code": to_key}]
        self.variable_name = variable_name
        self.extra_conditions = conditions or []
        self.options = options

    def build(self) -> dict[str, Any]:
        """Build simultaneous manipulator."""
        sim_options = {
            "detect_key_down_uninterruptedly": self.options.get(
                "detect_key_down_uninterruptedly", False
            ),
            "key_down_order": self.options.get("key_down_order", "insensitive"),
            "key_up_order": self.options.get("key_up_order", "insensitive"),
            "key_up_when": self.options.get("key_up_when", "any"),
        }

        filtered_options = {
            key: value
            for key, value in sim_options.items()
            if value
            and not (
                key in {"key_down_order", "key_up_order"} and value == "insensitive"
            )
            and not (key == "key_up_when" and value == "any")
        }

        result: dict[str, Any] = {
            "type": "basic",
            "from": {
                "simultaneous": [{"key_code": key} for key in self.combo_keys],
                "modifiers": {"optional": ["any"]},
            },
            "to": self.to_target,
            "conditions": [
                {"type": "variable_if", "name": self.variable_name, "value": 1},
                *self.extra_conditions,
            ],
        }

        if filtered_options:
            result["from"]["simultaneous_options"] = filtered_options

        to_after_key_up = self.options.get("to_after_key_up")
        if to_after_key_up is not None:
            result["to_after_key_up"] = to_after_key_up

        return result


class LayerStackBuilder:
    """Builder for layer-based key mappings."""

    def __init__(
        self,
        name: str,
        trigger_keys: str | list[str],
        to_if_alone: str | None = None,
    ):
        if not name:
            raise ValueError("Layer name cannot be empty")
        keys = trigger_keys if isinstance(trigger_keys, list) else [trigger_keys]
        if not keys:
            raise ValueError("trigger_keys cannot be empty")
        if any(not key for key in keys):
            raise ValueError("trigger_keys cannot contain empty keys")

        self.name = name
        self.trigger_keys = keys
        self.to_if_alone = to_if_alone

        self.mappings: list[tuple[str, str | dict[str, Any]]] = []
        self.combos: list[
            tuple[list[str], str | list[dict[str, Any]], dict[str, Any]]
        ] = []
        self.sequences: list[tuple[list[str], str]] = []
        self.sequence_timeout_ms = 500
        self.conditions: list[dict[str, Any]] = []

    def map(self, from_key: str, to_key: str | dict[str, Any]) -> LayerStackBuilder:
        """Add a simple key mapping within this layer."""
        if not from_key:
            raise ValueError("from_key cannot be empty")
        if isinstance(to_key, str) and not to_key:
            raise ValueError("to_key cannot be empty")
        self.mappings.append((from_key, to_key))
        return self

    def map_combo(
        self,
        combo_keys: list[str],
        to_key: str | list[dict[str, Any]],
        **options: Any,
    ) -> LayerStackBuilder:
        """Add a combo (simultaneous keys) mapping."""
        if len(combo_keys) < 2:
            raise ValueError("combo_keys must contain at least two keys")
        if any(not key for key in combo_keys):
            raise ValueError("combo_keys cannot contain empty keys")
        if isinstance(to_key, str) and not to_key:
            raise ValueError("to_key cannot be empty")
        self.combos.append((combo_keys, to_key, options))
        return self

    def map_sequence(self, seq_keys: list[str], to_key: str) -> LayerStackBuilder:
        """Add a sequence mapping."""
        if len(seq_keys) < 2:
            raise ValueError("seq_keys must contain at least two keys")
        if any(not key for key in seq_keys):
            raise ValueError("seq_keys cannot contain empty keys")
        if not to_key:
            raise ValueError("to_key cannot be empty")
        self.sequences.append((seq_keys, to_key))
        return self

    def map_macro(
        self,
        from_key: str,
        template_type: str = "typed_text",
        **params: Any,
    ) -> LayerStackBuilder:
        """Add a macro mapping using a template."""
        if not template_type:
            raise ValueError("template_type cannot be empty")
        self.mappings.append((from_key, {"template": template_type, "params": params}))
        return self

    def when_app(self, app_identifiers: str | list[str]) -> LayerStackBuilder:
        """Restrict this layer to specific apps."""
        apps = (
            [app_identifiers] if isinstance(app_identifiers, str) else app_identifiers
        )
        self.conditions.append(
            {
                "type": "frontmost_application_if",
                "bundle_identifiers": apps,
            }
        )
        return self

    def unless_app(self, app_identifiers: str | list[str]) -> LayerStackBuilder:
        """Exclude specific apps from this layer."""
        apps = (
            [app_identifiers] if isinstance(app_identifiers, str) else app_identifiers
        )
        self.conditions.append(
            {
                "type": "frontmost_application_unless",
                "bundle_identifiers": apps,
            }
        )
        return self

    def unless_variable(self, var_name: str, value: int = 1) -> LayerStackBuilder:
        """Exclude this layer if a variable has a specific value."""
        self.conditions.append(
            {
                "type": "variable_unless",
                "name": var_name,
                "value": value,
            }
        )
        return self

    def set_sequence_timeout(self, ms: int) -> LayerStackBuilder:
        """Set timeout for sequence mappings in milliseconds."""
        if ms <= 0:
            raise ValueError("Sequence timeout must be positive")
        self.sequence_timeout_ms = ms
        return self

    def build_rules(self) -> list[Rule]:
        """Build all rules for this layer."""
        return [
            self._build_activation_rule(),
            *self._build_mapping_rules(),
            *self._build_combo_rules(),
            *self._build_sequence_rules(),
        ]

    def _layer_conditions(self) -> list[dict[str, Any]]:
        return [
            {"type": "variable_if", "name": self.name, "value": 1},
            *self.conditions,
        ]

    def _build_rule(
        self,
        description: str,
        from_block: dict[str, Any],
        to_actions: list[dict[str, Any]],
        conditions: list[dict[str, Any]] | None = None,
        **extra: Any,
    ) -> Rule:
        manip: dict[str, Any] = {
            "type": "basic",
            "from": from_block,
            "to": to_actions,
        }
        if conditions:
            manip["conditions"] = conditions
        manip.update(extra)
        return Rule(description).add(RawManipulator(manip))

    def _build_activation_rule(self) -> Rule:
        if len(self.trigger_keys) == 1:
            key = self.trigger_keys[0]
            alone_key = self.to_if_alone or key
            return self._build_rule(
                f"{self.name} activation",
                {"key_code": key, "modifiers": {"optional": ["any"]}},
                [{"set_variable": {"name": self.name, "value": 1}}],
                to_after_key_up=[{"set_variable": {"name": self.name, "value": 0}}],
                to_if_alone=[{"key_code": alone_key}],
            )

        return self._build_rule(
            f"{self.name} stacked activation",
            {
                "simultaneous": [{"key_code": key} for key in self.trigger_keys],
                "modifiers": {"optional": ["any"]},
            },
            [{"set_variable": {"name": self.name, "value": 1}}],
            to_after_key_up=[{"set_variable": {"name": self.name, "value": 0}}],
        )

    def _build_mapping_rules(self) -> list[Rule]:
        rules: list[Rule] = []
        for from_key, to_target in self.mappings:
            from_block = {"key_code": from_key, "modifiers": {"optional": ["any"]}}
            conditions = self._layer_conditions()
            if isinstance(to_target, dict) and "template" in to_target:
                template_name = str(to_target["template"])
                to_actions = make_shell_command(template_name, **to_target["params"])
                description = f"{self.name} macro: {from_key} -> {template_name}"
            else:
                to_actions = (
                    [to_target]
                    if isinstance(to_target, dict)
                    else [{"key_code": to_target}]
                )
                description = f"{self.name}: {from_key} -> {to_target}"

            rules.append(
                self._build_rule(description, from_block, to_actions, conditions)
            )
        return rules

    def _build_combo_rules(self) -> list[Rule]:
        rules: list[Rule] = []
        for combo, to_target, options in self.combos:
            to_desc = to_target if isinstance(to_target, str) else "complex"
            manip = SimultaneousManipulator(
                combo,
                to_target,
                self.name,
                self.conditions,
                **options,
            )
            rules.append(
                Rule(f"{self.name} combo {'+'.join(combo)} -> {to_desc}").add(manip)
            )
        return rules

    def _build_sequence_rules(self) -> list[Rule]:
        rules: list[Rule] = []
        for seq, to_key in self.sequences:
            seq_name = f"{self.name}_seq_{'_'.join(seq)}"
            step_vars = [f"{seq_name}_step{index + 1}" for index in range(len(seq))]
            reset_all = [
                {"set_variable": {"name": var_name, "value": 0}}
                for var_name in step_vars
            ]

            for index, key in enumerate(seq):
                current_var = step_vars[index]
                conditions = self._layer_conditions()
                if index > 0:
                    conditions.append(
                        {
                            "type": "variable_if",
                            "name": step_vars[index - 1],
                            "value": 1,
                        }
                    )

                to_actions: list[dict[str, Any]] = [
                    {"set_variable": {"name": current_var, "value": 1}}
                ]
                if index == len(seq) - 1:
                    to_actions.append({"key_code": to_key})
                    to_actions.extend(reset_all)

                cancel_actions = [
                    {"set_variable": {"name": current_var, "value": 0}},
                ]
                if index > 0:
                    cancel_actions.append(
                        {"set_variable": {"name": step_vars[index - 1], "value": 0}}
                    )

                rules.append(
                    self._build_rule(
                        f"{self.name} sequence: {'+'.join(seq)}",
                        {"key_code": key, "modifiers": {"optional": ["any"]}},
                        to_actions,
                        conditions,
                        to_delayed_action={
                            "to_if_canceled": cancel_actions,
                            "to_if_invoked": [],
                        },
                        parameters={
                            "basic.to_delayed_action_delay_milliseconds": (
                                self.sequence_timeout_ms
                            )
                        },
                    )
                )

        return rules
