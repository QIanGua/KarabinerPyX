"""Quickstart example for the intent DSL."""

from __future__ import annotations

from karabinerpyx import IntentConfig


def get_config() -> IntentConfig:
    config = IntentConfig()
    profile = config.profile("Intent Quickstart")

    nav = profile.layer("nav", "right_command", tap="right_command")
    nav.map("h", "left_arrow")
    nav.map("j", "down_arrow")
    nav.map("k", "up_arrow")
    nav.map("l", "right_arrow")

    return config


config = get_config()
