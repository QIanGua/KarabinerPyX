from __future__ import annotations

import json
import sys
from pathlib import Path
import tempfile
from unittest.mock import patch

from karabinerpyx.cli import main


def test_cli_list(capsys):
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.py"
        config_path.write_text("""
from karabinerpyx import KarabinerConfig, Profile, Rule
profile = Profile("Test Profile")
profile.add_rule(Rule("Test Rule"))
config = KarabinerConfig().add_profile(profile)
""")

        with patch.object(sys, "argv", ["kpyx", "list", str(config_path)]):
            main()

        captured = capsys.readouterr()
        assert "Profile 1: Test Profile" in captured.out
        assert "1. Test Rule" in captured.out


def test_cli_build():
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.py"
        config_path.write_text("""
from karabinerpyx import KarabinerConfig, Profile
config = KarabinerConfig().add_profile(Profile("Test Profile"))
""")
        output_path = Path(tmpdir) / "output.json"

        with patch.object(
            sys, "argv", ["kpyx", "build", str(config_path), "-o", str(output_path)]
        ):
            main()

        assert output_path.exists()
        data = json.loads(output_path.read_text())
        assert data["profiles"][0]["name"] == "Test Profile"


def test_cli_dry_run(capsys):
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.py"
        config_path.write_text("""
from karabinerpyx import KarabinerConfig, Profile
config = KarabinerConfig().add_profile(Profile("Test Profile"))
""")

        with patch.object(sys, "argv", ["kpyx", "dry-run", str(config_path)]):
            main()

        captured = capsys.readouterr()
        assert (
            "New file would be created" in captured.out or "Changes for" in captured.out
        )
