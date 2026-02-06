# KarabinerPyX

**A Python DSL for Declarative, Safe, and Powerful Karabiner-Elements Configuration**

---

English | [中文](README.zh.md)

---

## 1. Overview

**KarabinerPyX** is a tool for **building Karabiner-Elements configuration (karabiner.json) via a Python DSL**.

Its goal is not to "generate JSON",
but to elevate keyboard mapping into a:

> **Composable, reusable, maintainable, and automatable configuration language**

---

## 2. Why KarabinerPyX?

### 2.1 Problems with Native Karabiner JSON

* JSON is verbose and deeply nested
* Hard to abstract layers / combos / sequences
* Lots of duplicated shell_command / AppleScript
* Easy to break configs when editing
* Applying changes is manual

---

### 2.2 Design Inspirations

KarabinerPyX synthesizes and extends ideas from:

| Project                | Inspiration                         |
| ---------------------- | ----------------------------------- |
| GokuRakuJoudo          | template abstraction, EDN-style DSL |
| karabiner.ts           | typed, composable config generation |
| Configuration as Code  | treat keyboard as input system code |

---

## 3. Design Philosophy

* **Configuration as Code**
* **Declarative over Imperative**
* **Composable Layers**
* **Safe by Default**: automatic backups (keep last 10), dry-run diff before apply
* **Automation First**: auto-sync docs on commit, one-command deploy

---

## 4. Feature Overview

### 4.1 Basic Mappings

* Single key mapping (A -> B)
* modifiers (mandatory / optional)
* tap / hold behavior (to_if_alone / to_if_held_down)

---

### 4.2 Layer System

#### 4.2.1 Hold Layer

```python
LayerStackBuilder("hyper", "right_command")
```

* press-and-hold to enter layer
* release to exit
* implemented via Karabiner variables

---

#### 4.2.2 Mapping Inside Layers

```python
hyper.map("j", "left_arrow")
hyper.map("k", "down_arrow")
```

---

### 4.3 Layer Stacking

#### 4.3.1 Multi-Trigger Layer

```python
LayerStackBuilder("hyper_alt", ["right_command", "right_option"])
```

* hold multiple layer keys together
* enter a new mode

**Typical Uses:**

* Hyper + Alt -> Window / Tiling Mode
* Hyper + Ctrl -> Dev Mode

---

### 4.4 Combo Mapping

```python
hyper.map_combo(["j", "k"], "escape")
```

* press multiple keys simultaneously
* uses Karabiner simultaneous

---

### 4.5 Sequence / Multi-Key Sequences

```python
hyper.map_sequence(["g", "g"], "home")
```

* press a sequence of keys
* triggers target action
* implemented with variable + delayed_action

#### 4.5.1 Timing Control

```python
hyper.set_sequence_timeout(500)  # ms
```

---

### 4.6 Macro System

#### 4.6.1 Multi key_code Macros

* one key triggers multiple key presses

---

#### 4.6.2 Typed Text Macro

```python
hyper.map_macro("t", template_type="typed_text", text="Hello, world!")
```

Use cases:

* common phrases
* code templates
* commit messages

---

## 5. Template-Based Macro (Core Abstraction)

### 5.1 Goals

Inspired by **GokuRakuJoudo :templates**:

* avoid hardcoding shell_command in mappings
* generate commands from templates

---

### 5.2 Template Definitions

```python
MACRO_TEMPLATES = {
  "typed_text": 'osascript -e \'tell application "System Events" to keystroke "{text}"\'',
  "alfred": 'osascript -e \'tell application id "com.runningwithcrayons.Alfred" to run trigger "{trigger}" in workflow "{workflow}" with argument "{arg}"\'',
  "keyboard_maestro": 'osascript -e \'tell application "Keyboard Maestro Engine" to do script "{script}"\'',
  "open": 'open "{path}"'
}
```

---

### 5.3 Usage

```python
hyper.map_macro(
  "a",
  template_type="alfred",
  trigger="search",
  workflow="MyWorkflow",
  arg="query"
)
```

---

## 6. Conditional Layers

### 6.1 App Conditions

```python
hyper.when_app([
  "com.apple.Terminal",
  "com.microsoft.VSCode"
])
```

* only active when target apps are foreground

---

## 7. Config Generation and Deployment

### 7.1 Automatic Backups (Safety First)

Before writing new config:

* backup existing `karabiner.json`
* timestamped filenames

```text
~/.config/karabiner/
  ├── karabiner.json
  ├── karabiner_backup_20251217_014233.json
```

---

### 7.2 JSON Validation

* parse check immediately after write
* prevents broken config

---

### 7.3 Auto Reload / Apply

```python
config.save(apply=True)
```

Internal steps:

1. backup old config
2. write new config
3. validate JSON
4. restart Karabiner via `launchctl kickstart`

No GUI needed.

---

## 8. CLI Tool (kpyx)

KarabinerPyX includes a CLI for managing configs:

- `kpyx list <script.py>`: list Profiles and Rules defined in a script.
- `kpyx build <script.py> -o output.json`: generate JSON.
- `kpyx dry-run <script.py>`: **recommended**, preview diff before apply.
- `kpyx apply <script.py>`: apply config (with backup and cleanup).
- `kpyx restore`: interactive restore from backups.
- `kpyx docs <script.py> -o CHEAT_SHEET.md`: generate Markdown docs.

### 8.1 Watch & Service

KarabinerPyX provides file watching and service mode:

```bash
# install optional dependency (watchfiles)
uv add "karabinerpyx[watch]"
# or
pip install "karabinerpyx[watch]"

# watch script changes and auto apply
kpyx watch path/to/config.py

# use default path or env var
export KPYX_CONFIG_FILE=~/.config/karabiner/config.py
kpyx watch

# install and start background service (launchd)
kpyx service install path/to/config.py

# check service status
kpyx service status

# uninstall service
kpyx service uninstall
```

Environment variables:

- `KPYX_CONFIG_FILE`: default config script path.
- `KPYX_WATCH_DEBOUNCE_MS`: debounce in ms (default 500).

---

## 9. Core Presets

KarabinerPyX includes common presets:

```python
from karabinerpyx.presets import hyper_key_rule, vim_navigation, common_system_shortcuts

# 1. Set Hyper Key (CapsLock -> Cmd+Ctrl+Opt+Shift)
profile.add_rule(hyper_key_rule())

# 2. Inject Vim navigation for any layer
hyper = LayerStackBuilder("hyper", "right_command")
vim_navigation(hyper)
```

---

## 10. Full Example

```python
from karabinerpyx import KarabinerConfig, Profile, LayerStackBuilder

hyper = (
    LayerStackBuilder("hyper", "right_command")
    .map("j", "left_arrow")
    .map("k", "down_arrow")
    .map_macro("t", template_type="typed_text", text="Hello from KarabinerPyX!")
)

profile = Profile("KarabinerPyX Demo")
for rule in hyper.build_rules():
    profile.add_rule(rule)

KarabinerConfig().add_profile(profile).save(apply=True)
```

---

## 11. Non-Functional Requirements

* High maintainability
* High extensibility
* Clear DSL semantics
* Future support for snapshot testing / diff / rollback

---

## 12. Out of Scope

* Not a replacement for Karabiner-Elements
* No GUI
* No bypassing Karabiner security model

---

## 13. Vision

> **Elevate keyboard mapping from "handwritten JSON"
> to a programmable human-interface design language.**

KarabinerPyX aims to serve:

* macOS power users
* engineers
* keyboard enthusiasts

as a **keyboard operating system DSL**.

---

## 14. License & Future

* MIT License (recommended)
* Roadmap:

  * dry-run / diff
  * auto rollback
  * preset layers
  * doc generation

---

**KarabinerPyX — Design your keyboard like you design software.**
