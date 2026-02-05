from __future__ import annotations

import plistlib
import subprocess

from karabinerpyx import service


def test_install_watch_service_creates_plist(monkeypatch, tmp_path):
    plist_path = tmp_path / "com.kpyx.watch.plist"
    log_path = tmp_path / "kpyx-watch.log"
    script_path = tmp_path / "config.py"
    script_path.write_text("config = None")

    monkeypatch.setattr(service, "PLIST_PATH", plist_path)
    monkeypatch.setattr(service, "LOG_PATH", log_path)
    monkeypatch.setattr(service, "sys", service.sys)
    monkeypatch.setattr(service.sys, "executable", "/usr/bin/python3")

    def fake_launchctl(args):
        return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

    monkeypatch.setattr(service, "_launchctl", fake_launchctl)

    service.install_watch_service(script_path, "argument")

    assert plist_path.exists()
    data = plistlib.loads(plist_path.read_bytes())
    assert data["Label"] == service.SERVICE_LABEL
    assert data["ProgramArguments"][-3:] == [
        "karabinerpyx.cli",
        "watch",
        str(script_path),
    ]
    assert data["StandardOutPath"] == str(log_path)
    assert data["StandardErrorPath"] == str(log_path)


def test_uninstall_watch_service(monkeypatch, tmp_path):
    plist_path = tmp_path / "com.kpyx.watch.plist"
    plist_path.write_text("test")
    monkeypatch.setattr(service, "PLIST_PATH", plist_path)

    calls: list[list[str]] = []

    def fake_launchctl(args):
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

    monkeypatch.setattr(service, "_launchctl", fake_launchctl)

    service.uninstall_watch_service()

    assert not plist_path.exists()
    assert ["stop", service.SERVICE_LABEL] in calls
    assert ["unload", str(plist_path)] in calls


def test_service_status_loaded(monkeypatch, capsys):
    def fake_launchctl(args):
        return subprocess.CompletedProcess(
            args,
            0,
            stdout=f"{service.SERVICE_LABEL}\n",
            stderr="",
        )

    monkeypatch.setattr(service, "_launchctl", fake_launchctl)
    service.service_status()
    captured = capsys.readouterr()
    assert "loaded" in captured.out
