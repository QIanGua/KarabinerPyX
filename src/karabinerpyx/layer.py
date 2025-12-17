"""Layer system for Karabiner configuration."""

from __future__ import annotations

from typing import Any

from karabinerpyx.models import Manipulator, Rule
from karabinerpyx.templates import make_shell_command


class SimultaneousManipulator(Manipulator):
    """A manipulator for simultaneous key presses."""

    def __init__(
        self,
        combo_keys: list[str],
        to_key: str,
        variable_name: str,
    ):
        super().__init__(combo_keys[0])
        self.combo_keys = combo_keys
        self.to_key = to_key
        self.variable_name = variable_name

    def build(self) -> dict[str, Any]:
        """Build the simultaneous manipulator dictionary."""
        return {
            "type": "basic",
            "from": {
                "simultaneous": [{"key_code": k} for k in self.combo_keys],
                "modifiers": {"optional": ["any"]},
            },
            "to": [{"key_code": self.to_key}],
            "conditions": [
                {"type": "variable_if", "name": self.variable_name, "value": 1}
            ],
        }


class LayerStackBuilder:
    """Builder for layer-based key mappings.

    A layer is activated by holding one or more trigger keys and allows
    defining custom key behaviors within that layer.
    """

    def __init__(self, name: str, trigger_keys: str | list[str]):
        """Initialize a layer.

        Args:
            name: Unique name for this layer (used as variable name).
            trigger_keys: Key(s) to hold to activate the layer.
        """
        self.name = name
        self.trigger_keys = (
            trigger_keys if isinstance(trigger_keys, list) else [trigger_keys]
        )
        self.mappings: list[tuple[str, str | dict[str, Any]]] = []
        self.combos: list[tuple[list[str], str]] = []
        self.sequences: list[tuple[list[str], str]] = []
        self.sequence_timeout_ms = 500
        self.app_conditions: list[dict[str, Any]] = []

    def map(self, from_key: str, to_key: str) -> LayerStackBuilder:
        """Add a simple key mapping within this layer.

        Args:
            from_key: Source key code.
            to_key: Target key code.
        """
        self.mappings.append((from_key, to_key))
        return self

    def map_combo(self, combo_keys: list[str], to_key: str) -> LayerStackBuilder:
        """Add a combo (simultaneous keys) mapping.

        Args:
            combo_keys: Keys that must be pressed together.
            to_key: Target key code.
        """
        self.combos.append((combo_keys, to_key))
        return self

    def map_sequence(self, seq_keys: list[str], to_key: str) -> LayerStackBuilder:
        """Add a sequence mapping.

        Args:
            seq_keys: Keys that must be pressed in order.
            to_key: Target key code.
        """
        self.sequences.append((seq_keys, to_key))
        return self

    def map_macro(
        self,
        from_key: str,
        template_type: str = "typed_text",
        **params: Any,
    ) -> LayerStackBuilder:
        """Add a macro mapping using a template.

        Args:
            from_key: Source key code.
            template_type: Template name (e.g., 'typed_text', 'alfred').
            **params: Parameters for the template.
        """
        self.mappings.append((from_key, {"template": template_type, "params": params}))
        return self

    def when_app(self, app_identifiers: str | list[str]) -> LayerStackBuilder:
        """Restrict this layer to specific apps.

        Args:
            app_identifiers: Bundle identifier(s) of the app(s).
        """
        if isinstance(app_identifiers, str):
            app_identifiers = [app_identifiers]
        self.app_conditions.append({
            "type": "frontmost_application_if",
            "bundle_identifiers": app_identifiers,
        })
        return self

    def set_sequence_timeout(self, ms: int) -> LayerStackBuilder:
        """Set the timeout for sequence mappings.

        Args:
            ms: Timeout in milliseconds.
        """
        self.sequence_timeout_ms = ms
        return self

    def build_rules(self) -> list[Rule]:
        """Build all rules for this layer."""
        rules: list[Rule] = []

        # Layer activation rule
        rules.append(self._build_activation_rule())

        # Regular mappings / macros
        rules.extend(self._build_mapping_rules())

        # Combo mappings
        rules.extend(self._build_combo_rules())

        # Sequence mappings
        rules.extend(self._build_sequence_rules())

        return rules

    def _build_activation_rule(self) -> Rule:
        """Build the layer activation rule."""
        if len(self.trigger_keys) == 1:
            # Single trigger key
            key = self.trigger_keys[0]
            activation = {
                "type": "basic",
                "from": {"key_code": key, "modifiers": {"optional": ["any"]}},
                "to": [{"set_variable": {"name": self.name, "value": 1}}],
                "to_after_key_up": [
                    {"set_variable": {"name": self.name, "value": 0}}
                ],
                "to_if_alone": [{"key_code": "escape"}],
            }
            return Rule(f"{self.name} activation").add_dict(activation)
        else:
            # Stacked layer: hold multiple trigger keys
            activation = {
                "type": "basic",
                "from": {
                    "simultaneous": [{"key_code": k} for k in self.trigger_keys]
                },
                "to": [{"set_variable": {"name": self.name, "value": 1}}],
                "to_after_key_up": [
                    {"set_variable": {"name": self.name, "value": 0}}
                ],
            }
            return Rule(f"{self.name} stacked activation").add_dict(activation)

    def _build_mapping_rules(self) -> list[Rule]:
        """Build rules for regular mappings and macros."""
        rules: list[Rule] = []
        for from_key, to_target in self.mappings:
            if isinstance(to_target, dict) and "template" in to_target:
                # Macro mapping
                rules.append(
                    Rule(f"{self.name} macro: {from_key} → {to_target['template']}")
                    .add_dict({
                        "type": "basic",
                        "from": {
                            "key_code": from_key,
                            "modifiers": {"optional": ["any"]},
                        },
                        "to": make_shell_command(
                            to_target["template"], **to_target["params"]
                        ),
                        "conditions": [
                            {"type": "variable_if", "name": self.name, "value": 1}
                        ]
                        + self.app_conditions,
                    })
                )
            else:
                # Simple key mapping
                rules.append(
                    Rule(f"{self.name}: {from_key} → {to_target}").add(
                        Manipulator(from_key).to(to_target).when_variable(self.name)
                    )
                )
        return rules

    def _build_combo_rules(self) -> list[Rule]:
        """Build rules for combo mappings."""
        rules: list[Rule] = []
        for combo, to_key in self.combos:
            rules.append(
                Rule(f"{self.name} combo {'+'.join(combo)} → {to_key}").add(
                    SimultaneousManipulator(combo, to_key, self.name)
                )
            )
        return rules

    def _build_sequence_rules(self) -> list[Rule]:
        """Build rules for sequence mappings."""
        rules: list[Rule] = []
        for seq, to_key in self.sequences:
            seq_name = f"{self.name}_seq_{'_'.join(seq)}"
            for i, key in enumerate(seq):
                next_var = f"{seq_name}_step{i + 1}"
                conds: list[dict[str, Any]] = [
                    {"type": "variable_if", "name": self.name, "value": 1}
                ] + self.app_conditions

                if i > 0:
                    conds.append({
                        "type": "variable_if",
                        "name": f"{seq_name}_step{i}",
                        "value": 1,
                    })

                manip: dict[str, Any] = {
                    "type": "basic",
                    "from": {"key_code": key, "modifiers": {"optional": ["any"]}},
                    "to": [{"set_variable": {"name": next_var, "value": 1}}],
                    "to_delayed_action": {
                        "to_if_canceled": [
                            {"set_variable": {"name": f"{seq_name}_step{i + 1}", "value": 0}},
                            {"set_variable": {"name": f"{seq_name}_step{i}", "value": 0}},
                        ],
                        "to_if_invoked": [],
                    },
                    "conditions": conds,
                    "parameters": {
                        "basic.to_delayed_action_delay_milliseconds": self.sequence_timeout_ms
                    },
                }

                # Last key in sequence triggers the actual action
                if i == len(seq) - 1:
                    manip["to"].append({"key_code": to_key})
                    manip["to"].append(
                        {"set_variable": {"name": f"{seq_name}_step{i + 1}", "value": 0}}
                    )
                    manip["to"].append(
                        {"set_variable": {"name": f"{seq_name}_step{i}", "value": 0}}
                    )

                rules.append(
                    Rule(f"{self.name} sequence: {'+'.join(seq)}").add_dict(manip)
                )

        return rules
