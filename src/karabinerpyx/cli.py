from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

from karabinerpyx.models import KarabinerConfig
from karabinerpyx.deploy import save_config
from karabinerpyx.docs import save_cheat_sheet


def load_config_from_script(script_path: str) -> KarabinerConfig:
    """Load KarabinerConfig from a Python script."""
    path = Path(script_path).resolve()
    if not path.exists():
        print(f"❌ Error: Script not found: {script_path}")
        sys.exit(1)

    # Add script directory to sys.path to allow relative imports
    sys.path.insert(0, str(path.parent))

    spec = importlib.util.spec_from_file_location("user_config", path)
    if spec is None or spec.loader is None:
        print(f"❌ Error: Could not load script: {script_path}")
        sys.exit(1)

    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as e:
        print(f"❌ Error executing script: {e}")
        sys.exit(1)

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

    print(f"❌ Error: No KarabinerConfig found in {script_path}")
    print("   Please define a 'config' variable or a 'get_config()' function.")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="KarabinerPyX CLI - Manage your Karabiner-Elements configuration."
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Build command
    build_parser = subparsers.add_parser("build", help="Build JSON from script")
    build_parser.add_argument("script", help="Path to Python config script")
    build_parser.add_argument(
        "-o", "--output", help="Output JSON path (default: karabiner.json)"
    )

    # Apply command
    apply_parser = subparsers.add_parser("apply", help="Apply config to Karabiner")
    apply_parser.add_argument("script", help="Path to Python config script")
    apply_parser.add_argument(
        "--no-backup", action="store_false", dest="backup", help="Skip backup"
    )
    apply_parser.set_defaults(backup=True)

    # Dry-run command
    dry_parser = subparsers.add_parser("dry-run", help="Show diff without applying")
    dry_parser.add_argument("script", help="Path to Python config script")

    # List command
    list_parser = subparsers.add_parser("list", help="List profiles and rules")
    list_parser.add_argument("script", help="Path to Python config script")

    # Docs command
    docs_parser = subparsers.add_parser("docs", help="Generate Markdown cheat sheet")
    docs_parser.add_argument("script", help="Path to Python config script")
    docs_parser.add_argument(
        "-o",
        "--output",
        default="CHEAT_SHEET.md",
        help="Output file (default: CHEAT_SHEET.md)",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    config = load_config_from_script(args.script)

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


if __name__ == "__main__":
    main()
