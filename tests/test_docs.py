from __future__ import annotations

import tempfile
from pathlib import Path

from karabinerpyx import KarabinerConfig, Manipulator, Profile, Rule
from karabinerpyx.docs import generate_html, generate_markdown, save_cheat_sheet


def test_generate_markdown():
    config = KarabinerConfig()
    profile = Profile("Test Profile")
    rule = Rule("Navigation")
    rule.add(Manipulator("h").to("left_arrow").when_app("com.apple.Terminal"))
    profile.add_rule(rule)
    config.add_profile(profile)

    md = generate_markdown(config)
    assert "# KarabinerPyX Mapping Cheat Sheet" in md
    assert "## Profile: Test Profile" in md
    assert "### Navigation" in md
    assert "| `h` | → `left_arrow` | App: com.apple.Terminal |" in md


def test_save_cheat_sheet():
    with tempfile.TemporaryDirectory() as tmpdir:
        config = KarabinerConfig()
        config.add_profile(Profile("Test"))
        output_path = Path(tmpdir) / "CHEATSHEET.md"

        save_cheat_sheet(config, output_path)
        assert output_path.exists()
        assert "# KarabinerPyX Mapping Cheat Sheet" in output_path.read_text()


def test_generate_html():
    config = KarabinerConfig()
    profile = Profile("Test Profile")
    rule = Rule("Navigation")
    rule.add(Manipulator("h").to("left_arrow"))
    profile.add_rule(rule)
    config.add_profile(profile)

    html = generate_html(config)
    assert "<title>KarabinerPyX Mapping Cheat Sheet</title>" in html
    assert "<h2>Profile: Test Profile (Selected)</h2>" in html
    assert "<h3>Navigation</h3>" in html
    assert "<code>h</code>" in html


def test_generate_markdown_combo():
    config = KarabinerConfig()
    profile = Profile("Test Profile")
    rule = Rule("Combo")
    rule.add_dict(
        {
            "type": "basic",
            "from": {"simultaneous": [{"key_code": "j"}, {"key_code": "k"}]},
            "to": [{"key_code": "escape"}],
            "conditions": [{"type": "variable_if", "name": "hyper", "value": 1}],
        }
    )
    profile.add_rule(rule)
    config.add_profile(profile)

    md = generate_markdown(config)
    assert "| `j + k` | → `escape` | Var: hyper==1 |" in md
