from __future__ import annotations

from karabinerpyx import KarabinerConfig, Profile, Rule
from karabinerpyx.analytics import compute_static_coverage, format_coverage_report


def test_analytics_conflict_and_formatting_paths():
    config = KarabinerConfig()
    profile = Profile("Default")

    profile.add_rule(
        Rule("combo-1").add_raw(
            {
                "type": "basic",
                "from": {
                    "simultaneous": [{"key_code": "j"}, {"key_code": "k"}],
                    "simultaneous_options": {"key_down_order": "strict"},
                },
                "to": [{"shell_command": "echo hi"}],
                "conditions": [{"type": "variable_if", "name": "hyper", "value": 1}],
            }
        )
    )

    profile.add_rule(
        Rule("combo-2").add_raw(
            {
                "type": "basic",
                "from": {
                    "simultaneous": [{"key_code": "j"}, {"key_code": "k"}],
                    "simultaneous_options": {"key_down_order": "strict"},
                },
                "to": [{"key_code": "escape"}],
                "conditions": [
                    {
                        "type": "frontmost_application_unless",
                        "bundle_identifiers": ["com.apple.Terminal"],
                    }
                ],
            }
        )
    )

    profile.add_rule(
        Rule("combo-3-duplicate").add_raw(
            {
                "type": "basic",
                "from": {
                    "simultaneous": [{"key_code": "j"}, {"key_code": "k"}],
                    "simultaneous_options": {"key_down_order": "strict"},
                },
                "to": [{"key_code": "tab"}],
                "conditions": [{"type": "variable_if", "name": "hyper", "value": 1}],
            }
        )
    )

    profile.add_rule(
        Rule("key-with-unknown-condition").add_raw(
            {
                "type": "basic",
                "from": {"key_code": "a", "modifiers": {"mandatory": ["shift"]}},
                "to": [{"key_code": "b"}],
                "conditions": [{"type": "mystery_condition"}],
            }
        )
    )

    config.add_profile(profile)

    report = compute_static_coverage(config)
    text = format_coverage_report(report)

    assert report["total_manipulators"] == 4
    assert report["macro_ratio"] > 0
    assert report["condition_branching_rate"] > 0
    assert len(report["unreachable_rules"]) == 1

    assert "Potential conflicts" in text
    assert "app_unless(com.apple.Terminal)" in text
    assert "mystery_condition" in text or "Conditions" in text
