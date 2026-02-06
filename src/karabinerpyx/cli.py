from __future__ import annotations

import argparse
import importlib.util
import os
import sys
from datetime import datetime
from pathlib import Path

from karabinerpyx.analytics import compute_static_coverage, format_coverage_report
from karabinerpyx.deploy import (
    DEFAULT_CONFIG_PATH,
    list_backups,
    reload_karabiner,
    restore_config,
    save_config,
)
from karabinerpyx.docs import save_cheat_sheet, save_cheat_sheet_html
from karabinerpyx.analytics import compute_static_coverage, format_coverage_report
from datetime import datetime
import time

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    Observer = None
    FileSystemEventHandler = object


def load_config_from_script(
    script_path: str, exit_on_error: bool = True
) -> KarabinerConfig | None:
    """Load KarabinerConfig from a Python script."""
    path = Path(script_path).resolve()
    if not path.exists():
        print(f"Error: Script not found: {script_path}")
        if exit_on_error:
            sys.exit(1)
        return None

    # Add script directory to sys.path to allow relative imports
    sys.path.insert(0, str(path.parent))

    spec = importlib.util.spec_from_file_location("user_config", path)
    if spec is None or spec.loader is None:
        print(f"Error: Could not load script: {script_path}")
        if exit_on_error:
            sys.exit(1)
        return None

    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as e:
        print(f"Error executing script: {e}")
        if exit_on_error:
            sys.exit(1)
        return None

    # Look for 'config' variable
    config = getattr(module, "config", None)
    if isinstance(config, KarabinerConfig):
        return config

    # Look for 'get_config' function
    get_config = getattr(module, "get_config", None)
    if callable(get_config):
        result = get_config()
        if isinstance(result, KarabinerConfig):
            return result

    # Try to find any KarabinerConfig instance in the module
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if isinstance(attr, KarabinerConfig):
            return attr

    print(f"Error: No KarabinerConfig found in {script_path}")
    print("   Please define a 'config' variable or a 'get_config()' function.")
    if exit_on_error:
        sys.exit(1)
    return None


def resolve_script_path(script_arg: str | None) -> tuple[Path, str]:
    """Resolve the script path from args, env, or default.

    Returns:
        (path, source) where source is "argument", "env", or "default".
    """
    if script_arg:
        return Path(script_arg).expanduser().resolve(), "argument"

    env_path = os.environ.get("KPYX_CONFIG_FILE")
    if env_path:
        return Path(env_path).expanduser().resolve(), "env"

    default_path = Path.home() / ".config" / "karabiner" / "config.py"
    if default_path.exists():
        return default_path, "default"

    print(
        "未提供脚本，且 KPYX_CONFIG_FILE 未设置，默认路径不存在："
        f"{default_path}"
    )
    sys.exit(1)


def parse_debounce_ms(value: str | None) -> int:
    """Parse debounce milliseconds from env or cli."""
    if value is None:
        env_value = os.environ.get("KPYX_WATCH_DEBOUNCE_MS")
        if env_value:
            value = env_value
    if value is None:
        return 500
    try:
        return max(0, int(value))
    except ValueError:
        print(f"Error: invalid debounce value: {value}")
        sys.exit(1)


def run_watch(script_path: Path, apply: bool, dry_run: bool, debounce_ms: int) -> None:
    """Watch a script and apply changes on updates."""
    try:
        from watchfiles import watch
    except Exception:
        print("Error: watchfiles is not installed. Install with:")
        print("  pip install 'karabinerpyx[watch]'")
        sys.exit(1)

    def execute_once() -> None:
        try:
            config = load_config_from_script(str(script_path), exit_on_error=False)
            if config is None:
                return
            save_config(config, apply=apply, dry_run=dry_run)
            stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if dry_run:
                print(f"Dry-run completed at {stamp}")
            else:
                print(f"Applied at {stamp}")
        except Exception as exc:
            print(f"Error: {exc}")

    execute_once()
    print(f"Watching: {script_path}")

    for _ in watch(script_path, script_path.parent, debounce=debounce_ms):
        execute_once()


def main():
    parser = argparse.ArgumentParser(
        description="KarabinerPyX CLI - Manage your Karabiner-Elements configuration."
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Build command
    build_parser = subparsers.add_parser("build", help="Build JSON from script")
    build_parser.add_argument(
        "script", nargs="?", help="Path to Python config script"
    )
    build_parser.add_argument(
        "-o", "--output", help="Output JSON path (default: karabiner.json)"
    )

    # Apply command
    apply_parser = subparsers.add_parser("apply", help="Apply config to Karabiner")
    apply_parser.add_argument(
        "script", nargs="?", help="Path to Python config script"
    )
    apply_parser.add_argument(
        "--no-backup", action="store_false", dest="backup", help="Skip backup"
    )
    apply_parser.set_defaults(backup=True)

    # Dry-run command
    dry_parser = subparsers.add_parser("dry-run", help="Show diff without applying")
    dry_parser.add_argument(
        "script", nargs="?", help="Path to Python config script"
    )

    # List command
    list_parser = subparsers.add_parser("list", help="List profiles and rules")
    list_parser.add_argument(
        "script", nargs="?", help="Path to Python config script"
    )

    # Docs command
    docs_parser = subparsers.add_parser("docs", help="Generate Markdown cheat sheet")
    docs_parser.add_argument(
        "script", nargs="?", help="Path to Python config script"
    )
    docs_parser.add_argument(
        "-o",
        "--output",
        default="CHEAT_SHEET.md",
        help="Output file (default: CHEAT_SHEET.md)",
    )
    # Docs HTML command
    docs_html_parser = subparsers.add_parser(
        "docs-html", help="Generate HTML cheat sheet"
    )
    docs_html_parser.add_argument(
        "script", nargs="?", help="Path to Python config script"
    )
    docs_html_parser.add_argument(
        "-o",
        "--output",
        default="CHEAT_SHEET.html",
        help="Output file (default: CHEAT_SHEET.html)",
    )

    # Stats command
    stats_parser = subparsers.add_parser(
        "stats", help="Show static coverage report"
    )
    stats_parser.add_argument(
        "script", nargs="?", help="Path to Python config script"
    )

    # Restore command
    restore_parser = subparsers.add_parser(
        "restore", help="Restore configuration from backup"
    )
    restore_parser.add_argument(
        "--index", type=int, help="Index of backup to restore (0 for latest)"
    )
    restore_parser.add_argument(
        "--apply", action="store_true", help="Reload Karabiner after restoring"
    )

    # Init command
    init_parser = subparsers.add_parser(
        "init", help="Create a starter configuration script"
    )
    init_parser.add_argument(
        "filename",
        nargs="?",
        default="karabiner_config.py",
        help="Filename to create (default: karabiner_config.py)",
    )

    # Watch command
    watch_parser = subparsers.add_parser(
        "watch", help="Watch script for changes and auto-apply"
    )
    watch_parser.add_argument("script", help="Path to Python config script")
    watch_parser.add_argument(
        "--no-backup", action="store_false", dest="backup", help="Skip backup"
    )
    watch_parser.set_defaults(backup=True)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "init":
        path = Path(args.filename)
        if path.exists():
            print(f"❌ Error: File {path} already exists.")
            sys.exit(1)

        template = """from karabinerpyx import (
    KarabinerConfig,
    Profile,
    LayerStackBuilder,
    Rule,
    Manipulator,
    CMD,
    OPT,
    SHIFT,
    CTRL,
)

# 1. Define Layers
# Example: Spacebar Layer (Tapping Spacebar sends Spacebar. Holding it activates 'nav' layer)
nav = LayerStackBuilder("nav", "spacebar")
nav.map("h", "left_arrow")
nav.map("j", "down_arrow")
nav.map("k", "up_arrow")
nav.map("l", "right_arrow")

# 2. Define Profile
profile = Profile("KarabinerPyX Config")

# Add layer rules
for rule in nav.build_rules():
    profile.add_rule(rule)

# Add a simple mapping example: Shift+Cmd+P -> Print Screen (example)
# profile.add_rule(
#     Rule("Screenshot").add(
#         Manipulator("p").modifiers([SHIFT, CMD]).to("print_screen")
#     )
# )

# 3. Create Config
config = KarabinerConfig()
config.add_profile(profile)
"""
        path.write_text(template)
        print(f"✅ Created starter config at {path}")
        print("Run 'kpyx apply' or 'kpyx watch' to start using it.")
        return

    if args.command == "watch":
        if Observer is None:
            print("❌ Error: 'watchdog' package is not installed.")
            print("Install it with: pip install watchdog")
            sys.exit(1)

        script_path = Path(args.script).resolve()
        if not script_path.exists():
            print(f"❌ Error: Script not found: {script_path}")
            sys.exit(1)

        print(f"👀 Watching {script_path} for changes...")

        # Apply once initially
        try:
            config = load_config_from_script(str(script_path))
            save_config(config, apply=True, backup=args.backup)
            print("✅ Initial config applied.")
        except Exception as e:
            print(f"❌ Error applying initial config: {e}")

        class Handler(FileSystemEventHandler):
            def __init__(self):
                self.last_run = 0

            def on_modified(self, event):
                if Path(event.src_path).resolve() == script_path:
                    # Debounce (0.5s)
                    if time.time() - self.last_run < 0.5:
                        return
                    self.last_run = time.time()

                    print(f"\n🔄 Detected change, reloading...")
                    try:
                        # Re-load config
                        new_config = load_config_from_script(str(script_path))
                        save_config(new_config, apply=True, backup=args.backup)
                        print("✅ Config applied successfully.")
                    except Exception as e:
                        print(f"❌ Error applying config: {e}")

        observer = Observer()
        observer.schedule(Handler(), str(script_path.parent), recursive=False)
        observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
        return

    if args.command == "restore":
        backups = list_backups()
        if not backups:
            print("No backups found.")
            return

        if args.index is not None:
            if 0 <= args.index < len(backups):
                target_backup = backups[args.index]
            else:
                print(
                    f"Invalid index: {args.index}. Available: 0 to {len(backups) - 1}"
                )
                return
        else:
            print("Available backups (newest first):")
            for i, b in enumerate(backups):
                mtime = datetime.fromtimestamp(b.stat().st_mtime).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                print(f"  [{i}] {b.name} ({mtime})")

            try:
                choice = input("\nSelect backup index to restore (or 'q' to quit): ")
                if choice.lower() == "q":
                    return
                idx = int(choice)
                if 0 <= idx < len(backups):
                    target_backup = backups[idx]
                else:
                    print("Invalid selection.")
                    return
            except (ValueError, EOFError, KeyboardInterrupt):
                print("\nCancelled.")
                return

        print(f"Restoring from {target_backup}...")
        if restore_config(target_backup):
            print(f"Configuration restored to {DEFAULT_CONFIG_PATH}")
            if args.apply:
                if reload_karabiner():
                    print("Karabiner configuration reloaded")
                else:
                    print("Failed to reload Karabiner (try manually)")
        else:
            print("Restoration failed.")
        return

    if args.command == "service":
        if args.service_command == "install":
            script_path, source = resolve_script_path(args.script)
            install_watch_service(script_path, source)
        elif args.service_command == "uninstall":
            uninstall_watch_service()
        elif args.service_command == "status":
            service_status()
        else:
            service_parser.print_help()
        return

    if args.command == "watch":
        script_path, source = resolve_script_path(args.script)
        debounce_ms = parse_debounce_ms(args.debounce)
        if source != "argument":
            print(f"Using script path from {source}: {script_path}")
        apply_mode = args.apply or not args.dry_run
        run_watch(
            script_path,
            apply=apply_mode,
            dry_run=args.dry_run,
            debounce_ms=debounce_ms,
        )
        return

    script_path, source = resolve_script_path(args.script)
    if source != "argument":
        print(f"Using script path from {source}: {script_path}")

    config = load_config_from_script(str(script_path))
    if config is None:
        return

    if args.command == "build":
        output = args.output or "karabiner.json"
        save_config(config, path=output, backup=False, apply=False)
    elif args.command == "apply":
        save_config(config, apply=True, backup=args.backup)
    elif args.command == "dry-run":
        save_config(config, dry_run=True)
    elif args.command == "list":
        print(f"📂 Configuration from {args.script}")
        for i, profile in enumerate(config.profiles, 1):
            status = " (selected)" if profile.selected else ""
            print(f"\n👤 Profile {i}: {profile.name}{status}")
            for j, rule in enumerate(profile.rules, 1):
                print(f"   {j}. {rule.description}")
    elif args.command == "docs":
        save_cheat_sheet(config, args.output)
    elif args.command == "docs-html":
        save_cheat_sheet_html(config, args.output)
    elif args.command == "stats":
        report = compute_static_coverage(config)
        print(format_coverage_report(report))


if __name__ == "__main__":
    main()
