from __future__ import annotations

from karabinerpyx import KarabinerConfig, Manipulator, Profile, Rule
from karabinerpyx.analytics import compute_static_coverage


def test_compute_static_coverage_duplicates():
    config = KarabinerConfig()
    profile = Profile("Default")

    rule_one = Rule("Rule One").add(Manipulator("h").to("left_arrow"))
    rule_two = Rule("Rule Two").add(Manipulator("h").to("home"))

    profile.add_rule(rule_one).add_rule(rule_two)
    config.add_profile(profile)

    report = compute_static_coverage(config)

    assert report["total_manipulators"] == 2
    assert report["unique_from"] == 1
    assert report["duplicate_from"] == 1
    assert "key(h)" in report["potential_conflicts"]
