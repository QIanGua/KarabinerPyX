from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from karabinerpyx.cli import main
from karabinerpyx.cli_commands import (
    CliError,
    load_config_from_script,
    parse_debounce_ms,
    run_watch,
)


def _write_script(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")


def test_main_help_without_command(capsys):
    assert main([]) == 0
    captured = capsys.readouterr()
    assert "KarabinerPyX CLI" in captured.out


def test_load_config_from_script_not_found():
    with pytest.raises(CliError):
        load_config_from_script("/tmp/does-not-exist.py")


def test_load_config_from_get_config(tmp_path):
    script = tmp_path / "config.py"
    _write_script(
        script,
        """
from karabinerpyx import KarabinerConfig, Profile

def get_config():
    return KarabinerConfig().add_profile(Profile("FromFunction"))
""",
    )
    config = load_config_from_script(str(script))
    assert config.profiles[0].name == "FromFunction"


def test_load_config_from_attribute_discovery(tmp_path):
    script = tmp_path / "config.py"
    _write_script(
        script,
        """
from karabinerpyx import KarabinerConfig, Profile
hidden = KarabinerConfig().add_profile(Profile("FromAttr"))
""",
    )
    config = load_config_from_script(str(script))
    assert config.profiles[0].name == "FromAttr"


def test_load_config_exec_error(tmp_path):
    script = tmp_path / "bad.py"
    _write_script(script, "raise RuntimeError('boom')")
    with pytest.raises(CliError):
        load_config_from_script(str(script))


def test_load_config_no_config(tmp_path):
    script = tmp_path / "bad.py"
    _write_script(script, "x = 1")
    with pytest.raises(CliError):
        load_config_from_script(str(script))


def test_parse_debounce_env_and_invalid(monkeypatch):
    monkeypatch.setenv("KPYX_WATCH_DEBOUNCE_MS", "321")
    assert parse_debounce_ms(None) == 321

    with pytest.raises(CliError):
        parse_debounce_ms("not-a-number")


def test_run_watch_missing_watchfiles(monkeypatch, tmp_path):
    script = tmp_path / "config.py"
    script.write_text("config = None", encoding="utf-8")
    monkeypatch.setitem(sys.modules, "watchfiles", SimpleNamespace())

    with pytest.raises(CliError):
        run_watch(script, apply=True, dry_run=False, debounce_ms=100)


def test_cli_service_usage_error(capsys):
    assert main(["service"]) == 1
    captured = capsys.readouterr()
    assert "Usage: kpyx service" in captured.out


def test_cli_restore_invalid_index(monkeypatch, capsys, tmp_path):
    backup = tmp_path / "backup.json"
    backup.write_text("{}", encoding="utf-8")

    monkeypatch.setattr("karabinerpyx.cli_commands.list_backups", lambda: [backup])
    assert main(["restore", "--index", "9"]) == 1
    captured = capsys.readouterr()
    assert "Invalid index" in captured.out


def test_cli_restore_interactive_quit(monkeypatch, tmp_path):
    backup = tmp_path / "backup.json"
    backup.write_text("{}", encoding="utf-8")

    monkeypatch.setattr("karabinerpyx.cli_commands.list_backups", lambda: [backup])
    monkeypatch.setattr("builtins.input", lambda _prompt: "q")

    assert main(["restore"]) == 0


def test_cli_restore_apply_reload_failure(monkeypatch, tmp_path):
    backup = tmp_path / "backup.json"
    backup.write_text("{}", encoding="utf-8")

    monkeypatch.setattr("karabinerpyx.cli_commands.list_backups", lambda: [backup])
    monkeypatch.setattr("karabinerpyx.cli_commands.restore_config", lambda _p: True)
    monkeypatch.setattr("karabinerpyx.cli_commands.reload_karabiner", lambda: False)

    assert main(["restore", "--index", "0", "--apply"]) == 1


def test_cli_watch_command_parameter_mapping(monkeypatch, tmp_path):
    script = tmp_path / "config.py"
    script.write_text("config = None", encoding="utf-8")

    captured: dict[str, object] = {}

    def fake_run_watch(
        script_path: Path,
        apply: bool,
        dry_run: bool,
        debounce_ms: int,
        backup: bool,
    ) -> None:
        captured["script"] = script_path
        captured["apply"] = apply
        captured["dry_run"] = dry_run
        captured["debounce_ms"] = debounce_ms
        captured["backup"] = backup

    monkeypatch.setattr("karabinerpyx.cli_commands.run_watch", fake_run_watch)

    assert (
        main(
            [
                "watch",
                str(script),
                "--dry-run",
                "--debounce-ms",
                "120",
                "--no-backup",
            ]
        )
        == 0
    )

    assert captured["script"] == script.resolve()
    assert captured["apply"] is False
    assert captured["dry_run"] is True
    assert captured["debounce_ms"] == 120
    assert captured["backup"] is False


def test_cli_docs_and_docs_html_commands(tmp_path):
    script = tmp_path / "config.py"
    _write_script(
        script,
        """
from karabinerpyx import KarabinerConfig, Profile
config = KarabinerConfig().add_profile(Profile("Docs"))
""",
    )

    md = tmp_path / "sheet.md"
    html = tmp_path / "sheet.html"

    assert main(["docs", str(script), "-o", str(md)]) == 0
    assert main(["docs-html", str(script), "-o", str(html)]) == 0
    assert md.exists()
    assert html.exists()


def test_cli_uses_env_script_path(monkeypatch, tmp_path):
    script = tmp_path / "config.py"
    _write_script(
        script,
        """
from karabinerpyx import KarabinerConfig, Profile
config = KarabinerConfig().add_profile(Profile("Env"))
""",
    )
    monkeypatch.setenv("KPYX_CONFIG_FILE", str(script))

    assert main(["list"]) == 0
