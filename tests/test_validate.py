"""Tests for semantic linting."""

from __future__ import annotations

from karabinerpyx import IntentConfig, KarabinerConfig, Manipulator, Profile, Rule
from karabinerpyx.validate import lint_intent, lint_karabiner_config


def test_lint_intent_reports_duplicate_mapping_error():
    config = IntentConfig()
    profile = config.profile("Lint")
    profile.map("a", "b")
    profile.map("a", "c")

    issues = lint_intent(config)
    assert any(issue.code == "duplicate_mapping" for issue in issues)
    assert any(issue.severity == "error" for issue in issues)


def test_lint_intent_allow_shadow_downgrades_duplicate():
    config = IntentConfig(allow_shadow=True)
    profile = config.profile("Lint")
    profile.map("a", "b")
    profile.map("a", "c")

    issues = lint_intent(config)
    assert any(issue.code == "shadowed_mapping" for issue in issues)
    assert not any(issue.code == "duplicate_mapping" for issue in issues)


def test_lint_intent_invalid_macro_params():
    config = IntentConfig()
    layer = config.profile("Lint").layer("nav", "right_command")
    layer.macro("t", "alfred", trigger="search")

    issues = lint_intent(config)
    assert any(issue.code == "invalid_macro" for issue in issues)


def test_lint_karabiner_reports_conflict_group_warning():
    profile = Profile("Conflict")
    profile.add_rule(
        Rule("one").add(
            Manipulator("a")
            .modifiers(optional=["any"])
            .to("b")
            .when_app("com.apple.Terminal")
        )
    )
    profile.add_rule(
        Rule("two").add(
            Manipulator("a")
            .modifiers(optional=["any"])
            .to("c")
            .unless_app("com.apple.Terminal")
        )
    )

    config = KarabinerConfig().add_profile(profile)
    issues = lint_karabiner_config(config)
    assert any(issue.code == "potential_conflict" for issue in issues)
