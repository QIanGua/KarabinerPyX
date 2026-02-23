"""Advanced intent DSL example with dual-role, combo, sequence, and macros."""

from __future__ import annotations

from karabinerpyx import IntentConfig


def get_config() -> IntentConfig:
    config = IntentConfig()
    profile = config.profile("Intent Advanced")

    profile.dual_role("caps_lock", tap="escape", hold="left_control")
    profile.map("semicolon", "quote")

    hyper = profile.layer("hyper", "right_command", tap="right_command")
    hyper.map("h", "left_arrow")
    hyper.map("j", "down_arrow")
    hyper.map("k", "up_arrow")
    hyper.map("l", "right_arrow")
    hyper.combo(["j", "k"], "escape")
    hyper.sequence(["g", "g"], "home", timeout_ms=300)
    hyper.macro("t", "typed_text", text="Hello from Intent DSL")

    terminal = profile.layer("terminal", "right_option")
    terminal.when_app(["^com\\.apple\\.Terminal$", "^com\\.googlecode\\.iterm2$"])
    terminal.map("c", "copy")
    terminal.map("v", "paste")

    return config


config = get_config()
