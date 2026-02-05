"""Launchd service management for KarabinerPyX watch."""

from __future__ import annotations

import plistlib
import subprocess
import sys
from pathlib import Path


SERVICE_LABEL = "com.kpyx.watch"
PLIST_PATH = Path.home() / "Library" / "LaunchAgents" / f"{SERVICE_LABEL}.plist"
LOG_PATH = Path.home() / "Library" / "Logs" / "kpyx-watch.log"


def _launchctl(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["launchctl", *args],
        check=False,
        capture_output=True,
        text=True,
    )


def _write_plist(script_path: Path) -> None:
    PLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    program = [
        sys.executable,
        "-m",
        "karabinerpyx.cli",
        "watch",
        str(script_path),
    ]

    plist_data = {
        "Label": SERVICE_LABEL,
        "ProgramArguments": program,
        "RunAtLoad": True,
        "KeepAlive": True,
        "StandardOutPath": str(LOG_PATH),
        "StandardErrorPath": str(LOG_PATH),
    }

    with PLIST_PATH.open("wb") as f:
        plistlib.dump(plist_data, f)


def install_watch_service(script_path: Path, source: str) -> None:
    """Install and start the watch service."""
    _write_plist(script_path)
    if source != "argument":
        print(f"Using script path from {source}: {script_path}")
    print(f"Installed plist: {PLIST_PATH}")

    load_result = _launchctl(["load", str(PLIST_PATH)])
    if load_result.returncode != 0:
        print("Failed to load service.")
        if load_result.stderr:
            print(load_result.stderr.strip())
        return

    start_result = _launchctl(["start", SERVICE_LABEL])
    if start_result.returncode != 0:
        print("Failed to start service.")
        if start_result.stderr:
            print(start_result.stderr.strip())
        return

    print("Service installed and started.")


def uninstall_watch_service() -> None:
    """Stop and remove the watch service."""
    if PLIST_PATH.exists():
        _launchctl(["stop", SERVICE_LABEL])
        _launchctl(["unload", str(PLIST_PATH)])
        PLIST_PATH.unlink(missing_ok=True)
        print("Service uninstalled.")
    else:
        print("Service is not installed.")


def service_status() -> None:
    """Show status of the watch service."""
    result = _launchctl(["list"])
    if result.returncode != 0:
        print("Failed to query launchctl.")
        if result.stderr:
            print(result.stderr.strip())
        return

    if SERVICE_LABEL in result.stdout:
        print("Service is loaded.")
    else:
        print("Service is not loaded.")
