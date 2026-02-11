from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from types import ModuleType

from karabinerpyx.analytics import compute_static_coverage, format_coverage_report
from karabinerpyx.cli_types import CliError
from karabinerpyx.deploy import (
    DEFAULT_CONFIG_PATH,
    list_backups,
    reload_karabiner,
    restore_config,
    save_config,
)
from karabinerpyx.docs import save_cheat_sheet, save_cheat_sheet_html
from karabinerpyx.models import KarabinerConfig
from karabinerpyx.service import (
    install_watch_service,
    service_status,
    uninstall_watch_service,
)


def load_config_from_script(script_path: str) -> KarabinerConfig:
    """Load KarabinerConfig from a Python script."""
    path = Path(script_path).expanduser().resolve()
    if not path.exists():
        raise CliError(f"Error: Script not found: {script_path}")

    module = _load_module(path)

    config = getattr(module, "config", None)
    if isinstance(config, KarabinerConfig):
        return config

    get_config = getattr(module, "get_config", None)
    if callable(get_config):
        result = get_config()
        if isinstance(result, KarabinerConfig):
            return result

    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if isinstance(attr, KarabinerConfig):
            return attr

    raise CliError(
        f"Error: No KarabinerConfig found in {script_path}\n"
        "Please define a 'config' variable or a 'get_config()' function."
    )


def _load_module(path: Path) -> ModuleType:
    module_name = f"karabinerpyx_user_config_{abs(hash(path))}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise CliError(f"Error: Could not load script: {path}")

    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent))
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        raise CliError(f"Error executing script: {exc}") from exc
    finally:
        if sys.path and sys.path[0] == str(path.parent):
            sys.path.pop(0)
    return module


def resolve_script_path(script_arg: str | None) -> tuple[Path, str]:
    """Resolve script path from arg, env, or default."""
    if script_arg:
        return Path(script_arg).expanduser().resolve(), "argument"

    env_path = os.environ.get("KPYX_CONFIG_FILE")
    if env_path:
        return Path(env_path).expanduser().resolve(), "env"

    default_path = Path.home() / ".config" / "karabiner" / "config.py"
    if default_path.exists():
        return default_path, "default"

    raise CliError(
        f"未提供脚本，且 KPYX_CONFIG_FILE 未设置，默认路径不存在：{default_path}"
    )


def parse_debounce_ms(value: str | None) -> int:
    """Parse debounce milliseconds from cli/env input."""
    resolved_value = value
    if resolved_value is None:
        env_value = os.environ.get("KPYX_WATCH_DEBOUNCE_MS")
        if env_value:
            resolved_value = env_value
    if resolved_value is None:
        return 500

    try:
        return max(0, int(resolved_value))
    except ValueError as exc:
        raise CliError(f"Error: invalid debounce value: {resolved_value}") from exc


def run_watch(
    script_path: Path,
    apply: bool,
    dry_run: bool,
    debounce_ms: int,
    backup: bool = True,
) -> None:
    """Watch script and auto-build/apply config."""
    try:
        from watchfiles import watch
    except Exception as exc:
        raise CliError(
            "Error: watchfiles is not installed. Install with:\n"
            "  pip install 'karabinerpyx[watch]'"
        ) from exc

    def execute_once() -> None:
        try:
            config = load_config_from_script(str(script_path))
            result = save_config(config, apply=apply, dry_run=dry_run, backup=backup)
            stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            mode = "Dry-run completed" if result.dry_run else "Applied"
            print(f"{mode} at {stamp}")
        except CliError as exc:
            print(exc)

    execute_once()
    print(f"Watching: {script_path}")

    for _changes in watch(script_path, script_path.parent, debounce=debounce_ms):
        execute_once()


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser."""
    parser = argparse.ArgumentParser(
        description="KarabinerPyX CLI - Manage your Karabiner configuration."
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    build_parser = subparsers.add_parser("build", help="Build JSON from script")
    build_parser.add_argument("script", nargs="?", help="Path to config script")
    build_parser.add_argument("-o", "--output", help="Output JSON path")

    apply_parser = subparsers.add_parser("apply", help="Apply config")
    apply_parser.add_argument("script", nargs="?", help="Path to config script")
    apply_parser.add_argument(
        "--no-backup",
        action="store_false",
        dest="backup",
        help="Skip backup",
    )
    apply_parser.set_defaults(backup=True)

    dry_parser = subparsers.add_parser("dry-run", help="Show diff only")
    dry_parser.add_argument("script", nargs="?", help="Path to config script")

    list_parser = subparsers.add_parser("list", help="List profiles and rules")
    list_parser.add_argument("script", nargs="?", help="Path to config script")

    docs_parser = subparsers.add_parser("docs", help="Generate Markdown docs")
    docs_parser.add_argument("script", nargs="?", help="Path to config script")
    docs_parser.add_argument("-o", "--output", default="CHEAT_SHEET.md")

    html_parser = subparsers.add_parser("docs-html", help="Generate HTML docs")
    html_parser.add_argument("script", nargs="?", help="Path to config script")
    html_parser.add_argument("-o", "--output", default="CHEAT_SHEET.html")

    stats_parser = subparsers.add_parser("stats", help="Show static coverage report")
    stats_parser.add_argument("script", nargs="?", help="Path to config script")
    stats_parser.add_argument("--json", action="store_true", dest="as_json")

    restore_parser = subparsers.add_parser("restore", help="Restore from backup")
    restore_parser.add_argument("--index", type=int)
    restore_parser.add_argument("--apply", action="store_true")

    init_parser = subparsers.add_parser("init", help="Create starter script")
    init_parser.add_argument("filename", nargs="?", default="karabiner_config.py")

    watch_parser = subparsers.add_parser("watch", help="Watch and apply changes")
    watch_parser.add_argument("script", nargs="?", help="Path to config script")
    watch_parser.add_argument("--apply", action="store_true")
    watch_parser.add_argument("--dry-run", action="store_true")
    watch_parser.add_argument("--debounce-ms", dest="debounce_ms")
    watch_parser.add_argument(
        "--no-backup",
        action="store_false",
        dest="backup",
        help="Skip backup",
    )
    watch_parser.set_defaults(backup=True)

    service_parser = subparsers.add_parser("service", help="Manage launchd service")
    service_sub = service_parser.add_subparsers(dest="service_command")

    service_install = service_sub.add_parser("install", help="Install service")
    service_install.add_argument("script", nargs="?", help="Path to config script")

    service_sub.add_parser("uninstall", help="Uninstall service")
    service_sub.add_parser("status", help="Service status")

    return parser


def run(argv: list[str] | None = None) -> int:
    """Run CLI and return process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    try:
        return _dispatch(args)
    except CliError as exc:
        print(exc)
        return exc.exit_code


def _dispatch(args: argparse.Namespace) -> int:
    special_handlers = {
        "init": lambda: _cmd_init(args),
        "restore": lambda: _cmd_restore(args),
        "service": lambda: _cmd_service(args),
        "watch": lambda: _cmd_watch(args),
    }
    if args.command in special_handlers:
        return special_handlers[args.command]()

    script_path, source = resolve_script_path(args.script)
    if source != "argument":
        print(f"Using script path from {source}: {script_path}")

    config = load_config_from_script(str(script_path))
    return _dispatch_with_config(args, script_path, config)


def _dispatch_with_config(
    args: argparse.Namespace,
    script_path: Path,
    config: KarabinerConfig,
) -> int:
    if args.command == "build":
        output = args.output or "karabiner.json"
        result = save_config(config, path=output, backup=False, apply=False)
        print(f"Karabiner config written to {result.path}")
        return 0

    if args.command == "apply":
        result = save_config(config, apply=True, backup=args.backup)
        print(f"Karabiner config written to {result.path}")
        if result.reload_status is False:
            print("Failed to reload Karabiner (try manually)")
            return 1
        return 0

    if args.command == "dry-run":
        save_config(config, dry_run=True)
        return 0

    if args.command == "list":
        print(f"Configuration from {script_path}")
        for profile_index, profile in enumerate(config.profiles, 1):
            status = " (selected)" if profile.selected else ""
            print(f"\nProfile {profile_index}: {profile.name}{status}")
            for rule_index, rule in enumerate(profile.rules, 1):
                print(f"  {rule_index}. {rule.description}")
        return 0

    if args.command == "docs":
        save_cheat_sheet(config, args.output)
        return 0

    if args.command == "docs-html":
        save_cheat_sheet_html(config, args.output)
        return 0

    if args.command == "stats":
        report = compute_static_coverage(config)
        if args.as_json:
            print(json.dumps(report, indent=2, ensure_ascii=False))
        else:
            print(format_coverage_report(report))
        return 0

    raise CliError(f"Unknown command: {args.command}", exit_code=2)


def _cmd_init(args: argparse.Namespace) -> int:
    path = Path(args.filename)
    if path.exists():
        raise CliError(f"Error: File {path} already exists.")

    template = """from karabinerpyx import KarabinerConfig, LayerStackBuilder, Profile

nav = LayerStackBuilder("nav", "spacebar")
nav.map("h", "left_arrow")
nav.map("j", "down_arrow")
nav.map("k", "up_arrow")
nav.map("l", "right_arrow")

profile = Profile("KarabinerPyX Config")
for rule in nav.build_rules():
    profile.add_rule(rule)

config = KarabinerConfig().add_profile(profile)
"""
    path.write_text(template, encoding="utf-8")
    print(f"Created starter config at {path}")
    print("Run 'kpyx apply' or 'kpyx watch' to start using it.")
    return 0


def _cmd_restore(args: argparse.Namespace) -> int:
    backups = list_backups()
    if not backups:
        print("No backups found.")
        return 0

    target_backup: Path
    if args.index is not None:
        if 0 <= args.index < len(backups):
            target_backup = backups[args.index]
        else:
            max_index = len(backups) - 1
            raise CliError(f"Invalid index: {args.index}. Available: 0 to {max_index}")
    else:
        print("Available backups (newest first):")
        for index, backup in enumerate(backups):
            timestamp = datetime.fromtimestamp(backup.stat().st_mtime)
            mtime = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            print(f"  [{index}] {backup.name} ({mtime})")

        try:
            choice = input("\nSelect backup index to restore (or 'q' to quit): ")
        except (EOFError, KeyboardInterrupt):
            print("\nCancelled.")
            return 1

        if choice.lower() == "q":
            return 0

        try:
            selected = int(choice)
        except ValueError as exc:
            raise CliError("Invalid selection.") from exc

        if not (0 <= selected < len(backups)):
            raise CliError("Invalid selection.")
        target_backup = backups[selected]

    print(f"Restoring from {target_backup}...")
    if not restore_config(target_backup):
        raise CliError("Restoration failed.")

    print(f"Configuration restored to {DEFAULT_CONFIG_PATH}")
    if args.apply:
        if reload_karabiner():
            print("Karabiner configuration reloaded")
        else:
            raise CliError("Failed to reload Karabiner (try manually)")

    return 0


def _cmd_service(args: argparse.Namespace) -> int:
    if args.service_command == "install":
        script_path, source = resolve_script_path(args.script)
        install_watch_service(script_path, source)
        return 0

    if args.service_command == "uninstall":
        uninstall_watch_service()
        return 0

    if args.service_command == "status":
        service_status()
        return 0

    raise CliError("Usage: kpyx service [install|status|uninstall]")


def _cmd_watch(args: argparse.Namespace) -> int:
    script_path, source = resolve_script_path(args.script)
    if source != "argument":
        print(f"Using script path from {source}: {script_path}")

    debounce_ms = parse_debounce_ms(args.debounce_ms)
    apply_mode = args.apply or not args.dry_run
    run_watch(
        script_path,
        apply=apply_mode,
        dry_run=args.dry_run,
        debounce_ms=debounce_ms,
        backup=args.backup,
    )
    return 0
