from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from karabinerpyx.cli import main, resolve_script_path, run_watch


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


def test_resolve_script_path_argument(tmp_path):
    script_path = tmp_path / "config.py"
    script_path.write_text("config = None")
    resolved, source = resolve_script_path(str(script_path))
    assert resolved == script_path.resolve()
    assert source == "argument"


def test_resolve_script_path_env(monkeypatch, tmp_path):
    script_path = tmp_path / "config.py"
    script_path.write_text("config = None")
    monkeypatch.setenv("KPYX_CONFIG_FILE", str(script_path))
    resolved, source = resolve_script_path(None)
    assert resolved == script_path.resolve()
    assert source == "env"


def test_resolve_script_path_default(monkeypatch, tmp_path):
    home_dir = tmp_path / "home"
    default_path = home_dir / ".config" / "karabiner" / "config.py"
    default_path.parent.mkdir(parents=True, exist_ok=True)
    default_path.write_text("config = None")
    monkeypatch.setattr(
        "karabinerpyx.cli.Path.home",
        lambda: home_dir,
    )
    resolved, source = resolve_script_path(None)
    assert resolved == default_path
    assert source == "default"


def test_resolve_script_path_missing(monkeypatch, tmp_path, capsys):
    home_dir = tmp_path / "home"
    monkeypatch.delenv("KPYX_CONFIG_FILE", raising=False)
    monkeypatch.setattr("karabinerpyx.cli.Path.home", lambda: home_dir)
    with pytest.raises(SystemExit):
        resolve_script_path(None)
    captured = capsys.readouterr()
    assert "默认路径不存在" in captured.out


def test_run_watch_executes_on_changes(monkeypatch, tmp_path):
    script_path = tmp_path / "config.py"
    script_path.write_text("config = None")

    calls: list[str] = []

    def fake_load(path: str, exit_on_error: bool = True):
        return object()

    def fake_save(config, apply: bool, dry_run: bool):
        calls.append("save")

    def fake_watch(*args, **kwargs):
        yield {"change"}

    monkeypatch.setattr("karabinerpyx.cli.load_config_from_script", fake_load)
    monkeypatch.setattr("karabinerpyx.cli.save_config", fake_save)
    monkeypatch.setitem(
        sys.modules, "watchfiles", SimpleNamespace(watch=fake_watch)
    )

    run_watch(script_path, apply=True, dry_run=False, debounce_ms=100)
    assert len(calls) == 2
