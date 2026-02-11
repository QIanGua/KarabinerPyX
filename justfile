# KarabinerPyX development tasks

default:
    @just --list

init:
    uv sync --all-extras

install:
    uv sync

install-dev:
    uv sync --extra dev

test:
    uv run pytest tests/ -v

test-cov:
    uv run pytest tests/ -v --cov=src/karabinerpyx --cov-report=term-missing

typecheck:
    uv run mypy src/karabinerpyx

example:
    uv run python examples/demo.py

docs:
    uv run kpyx docs examples/demo.py -o CHEAT_SHEET.md
    uv run kpyx docs examples/presets_usage.py -o PRESETS_CHEAT_SHEET.md
    uv run kpyx docs examples/my_personal_config.py -o PERSONAL_CHEAT_SHEET.md

check: fmt lint typecheck test docs
    @echo "All checks passed and documentation updated"

restore:
    uv run kpyx restore

build:
    uv build

clean:
    rm -rf dist/ build/ *.egg-info src/*.egg-info .pytest_cache .coverage
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

fmt:
    uv run ruff format src/ tests/

lint:
    uv run ruff check src/ tests/
