from __future__ import annotations

from pathlib import Path
import tempfile
from karabinerpyx import KarabinerConfig, Profile, Rule, Manipulator
from karabinerpyx.docs import generate_markdown, save_cheat_sheet

def test_generate_markdown():
    config = KarabinerConfig()
    profile = Profile("Test Profile")
    rule = Rule("Navigation")
    rule.add(Manipulator("h").to("left_arrow").when_app("com.apple.Terminal"))
    profile.add_rule(rule)
    config.add_profile(profile)
    
    md = generate_markdown(config)
    assert "# ⌨️ KarabinerPyX Mapping Cheat Sheet" in md
    assert "## 👤 Profile: Test Profile" in md
    assert "### 📜 Navigation" in md
    assert "| `h` | → `left_arrow` | App: com.apple.Terminal |" in md

def test_save_cheat_sheet():
    with tempfile.TemporaryDirectory() as tmpdir:
        config = KarabinerConfig()
        config.add_profile(Profile("Test"))
        output_path = Path(tmpdir) / "CHEATSHEET.md"
        
        save_cheat_sheet(config, output_path)
        assert output_path.exists()
        assert "# ⌨️ KarabinerPyX Mapping Cheat Sheet" in output_path.read_text()
