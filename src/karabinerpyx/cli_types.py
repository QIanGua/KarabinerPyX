from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ResolvedScriptPath:
    """Resolved script path with resolution source."""

    path: Path
    source: str


class CliError(Exception):
    """CLI error carrying exit code."""

    def __init__(self, message: str, exit_code: int = 1):
        super().__init__(message)
        self.exit_code = exit_code
