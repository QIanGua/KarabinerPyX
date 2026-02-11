from __future__ import annotations

from karabinerpyx import cli_commands as _commands

load_config_from_script = _commands.load_config_from_script
parse_debounce_ms = _commands.parse_debounce_ms
resolve_script_path = _commands.resolve_script_path
run_watch = _commands.run_watch


__all__ = [
    "load_config_from_script",
    "parse_debounce_ms",
    "resolve_script_path",
    "run_watch",
    "main",
]


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""
    return _commands.run(argv)


if __name__ == "__main__":
    raise SystemExit(main())
