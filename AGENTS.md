# AGENTS.md - Development Guide for KarabinerPyX

This document provides essential information for agentic AI assistants (like Claude, Cursor, or Copilot) working on the KarabinerPyX codebase.

## 1. Project Overview
KarabinerPyX is a Python DSL for declarative, safe, and powerful Karabiner-Elements configuration. It allows users to define keyboard mappings using a fluent Python API instead of manual JSON editing.

## 2. Environment & Tooling
- **Python**: 3.10+
- **Package Manager**: [uv](https://github.com/astral-sh/uv)
- **Task Runner**: [just](https://github.com/casey/just)
- **Linter/Formatter**: [ruff](https://github.com/astral-sh/ruff)
- **Test Framework**: [pytest](https://docs.pytest.org/)

### Common Commands
```bash
# Initialize environment
just init

# Install dependencies
just install

# Run all tests
just test

# Run tests with coverage
just test-cov

# Run a single test file
uv run pytest tests/test_models.py

# Run a specific test case
uv run pytest tests/test_models.py::TestManipulator::test_simple_mapping

# Lint and Format
just lint
just fmt

# Run example/demo
just example
```

## 3. Code Style Guidelines
Follow these conventions strictly to maintain consistency with the existing codebase:

### Type Safety
- **Mandatory Type Hints**: Use type hints for all function arguments and return types.
- **Annotations**: Always include `from __future__ import annotations` at the top of files.
- **Generics**: Use standard collection types (e.g., `list[str]`, `dict[str, Any]`) instead of `typing.List` or `typing.Dict`.
- **Any**: Use `Any` sparingly, primarily for complex JSON structures.

### Formatting & Naming
- **Style**: Follow PEP 8 via `ruff`.
- **Classes**: `CamelCase` (e.g., `LayerStackBuilder`, `Manipulator`).
- **Methods/Variables**: `snake_case` (e.g., `map_combo`, `trigger_keys`).
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_PATH`, `MACRO_TEMPLATES`).
- **Fluent API**: Methods that modify an object should return `self` to allow chaining (e.g., `manipulator.to("b").when_app("...")`).

### Imports
Order:
1. Future imports (`from __future__ import annotations`)
2. Standard library
3. Third-party libraries
4. Local project modules

### Documentation
- Use triple double-quotes (`"""`) for docstrings.
- Include a summary line.
- Document arguments and return values for public API methods.

## 4. Architecture & Patterns
- **Declarative DSL**: Focus on building a data structure that represents the Karabiner JSON.
- **Separation of Concerns**:
  - `models.py`: Low-level Karabiner primitives (`Manipulator`, `Rule`, `Profile`).
  - `layer.py`: High-level abstractions for layers, combos, and sequences.
  - `templates.py`: Reusable shell command templates.
  - `deploy.py`: Logic for saving, backing up, and reloading Karabiner.
- **Safety First**: Always backup existing `karabiner.json` before overwriting. Use timestamped filenames.

## 5. Performance Principles (from CLAUDE.md)
- **Fully Optimized**: Maximize big-O efficiency for memory and runtime.
- **Vectorization**: Prefer built-ins and efficient data structures.
- **Avoid Loops**: Use generator expressions or list comprehensions where appropriate.
- **Measure**: Add benchmarks for hot paths before optimizing.

## 6. Error Handling
- Use precise exception catching with context.
- Provide meaningful error messages.
- Defensive programming for edge cases (e.g., checking if paths exist).

## 7. Testing Strategy
- **Unit Tests**: Test each model and builder class in isolation.
- **Integration Tests**: Verify the full pipeline from DSL to generated JSON.
- **Assertions**: Verify the structure of the generated dictionary against the Karabiner schema.

## 8. Development Constraints
- **No Emojis**: Do not use emojis in code or commit messages.
- **Present Tense**: Use present tense for commit messages (e.g., "Add layer stacking support").
- **Minimal Changes**: Fix bugs minimally; avoid unnecessary refactoring during bug fixes.
- **No Suppression**: Never use `as any`, `@ts-ignore`, or `@ts-expect-error` to hide type errors.

## 9. Cursor/Copilot Instructions
If you are using Cursor or Copilot, adhere to the rules defined in this file. This project emphasizes "Configuration as Code" and "Safe by Default" principles.
