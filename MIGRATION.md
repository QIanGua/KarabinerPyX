# Migration Guide: v0.1 to v0.2

This guide lists breaking and transitional changes introduced in KarabinerPyX v0.2.

## API changes

1. `Rule.add_raw()` is the new low-level dictionary entrypoint.
2. `Rule.add_dict()` still works, but is deprecated and emits `DeprecationWarning`.
3. `deploy.save_config()` now returns a `SaveResult` object instead of a `Path`.
4. `KarabinerConfig.save()` is still available for compatibility and returns `Path`, but is deprecated.
5. `LayerStackBuilder` now validates inputs strictly:
- empty trigger key list is rejected
- combo length must be at least 2
- sequence length must be at least 2
- sequence timeout must be positive

## CLI changes

1. CLI internals moved to `karabinerpyx.cli_commands` and `karabinerpyx.cli_types`.
2. `watch` is now a single implementation based on `watchfiles`.
3. `watch` supports unified options:
- `--apply`
- `--dry-run`
- `--debounce-ms`
- `--no-backup`
4. `stats` now supports machine-readable output:
- `kpyx stats <script.py> --json`
5. `service` commands are now fully wired:
- `kpyx service install [script.py]`
- `kpyx service status`
- `kpyx service uninstall`

## Example migration

### Old

```python
rule = Rule("Raw")
rule.add_dict({"type": "basic", "from": {"key_code": "a"}, "to": [{"key_code": "b"}]})
```

### New

```python
rule = Rule("Raw")
rule.add_raw({"type": "basic", "from": {"key_code": "a"}, "to": [{"key_code": "b"}]})
```

### Old

```python
path = save_config(config)
```

### New

```python
result = save_config(config)
path = result.path
```

## Transition window

Deprecated compatibility shims are retained for one release cycle after v0.2.
