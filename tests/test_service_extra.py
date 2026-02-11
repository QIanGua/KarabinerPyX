from __future__ import annotations

import subprocess

from karabinerpyx import service


def test_install_watch_service_load_failure(monkeypatch, tmp_path, capsys):
    plist_path = tmp_path / "com.kpyx.watch.plist"
    log_path = tmp_path / "kpyx-watch.log"
    script_path = tmp_path / "config.py"
    script_path.write_text("config = None", encoding="utf-8")

    monkeypatch.setattr(service, "PLIST_PATH", plist_path)
    monkeypatch.setattr(service, "LOG_PATH", log_path)
    monkeypatch.setattr(service, "sys", service.sys)
    monkeypatch.setattr(service.sys, "executable", "/usr/bin/python3")

    def fake_launchctl(args):
        if args[0] == "load":
            return subprocess.CompletedProcess(args, 1, stdout="", stderr="bad-load")
        return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

    monkeypatch.setattr(service, "_launchctl", fake_launchctl)

    service.install_watch_service(script_path, "env")
    captured = capsys.readouterr()
    assert "Failed to load service" in captured.out
    assert "bad-load" in captured.out


def test_install_watch_service_start_failure(monkeypatch, tmp_path, capsys):
    plist_path = tmp_path / "com.kpyx.watch.plist"
    log_path = tmp_path / "kpyx-watch.log"
    script_path = tmp_path / "config.py"
    script_path.write_text("config = None", encoding="utf-8")

    monkeypatch.setattr(service, "PLIST_PATH", plist_path)
    monkeypatch.setattr(service, "LOG_PATH", log_path)
    monkeypatch.setattr(service, "sys", service.sys)
    monkeypatch.setattr(service.sys, "executable", "/usr/bin/python3")

    def fake_launchctl(args):
        if args[0] == "start":
            return subprocess.CompletedProcess(args, 1, stdout="", stderr="bad-start")
        return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

    monkeypatch.setattr(service, "_launchctl", fake_launchctl)

    service.install_watch_service(script_path, "argument")
    captured = capsys.readouterr()
    assert "Failed to start service" in captured.out
    assert "bad-start" in captured.out


def test_uninstall_watch_service_when_not_installed(monkeypatch, tmp_path, capsys):
    plist_path = tmp_path / "missing.plist"
    monkeypatch.setattr(service, "PLIST_PATH", plist_path)
    service.uninstall_watch_service()
    captured = capsys.readouterr()
    assert "not installed" in captured.out


def test_service_status_failure(monkeypatch, capsys):
    def fake_launchctl(args):
        return subprocess.CompletedProcess(args, 1, stdout="", stderr="list-failed")

    monkeypatch.setattr(service, "_launchctl", fake_launchctl)
    service.service_status()
    captured = capsys.readouterr()
    assert "Failed to query launchctl" in captured.out
    assert "list-failed" in captured.out


def test_service_status_not_loaded(monkeypatch, capsys):
    def fake_launchctl(args):
        return subprocess.CompletedProcess(args, 0, stdout="other.service", stderr="")

    monkeypatch.setattr(service, "_launchctl", fake_launchctl)
    service.service_status()
    captured = capsys.readouterr()
    assert "not loaded" in captured.out
