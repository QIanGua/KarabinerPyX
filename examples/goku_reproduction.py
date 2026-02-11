from __future__ import annotations

from karabinerpyx import KarabinerConfig, LayerStackBuilder, Manipulator, Profile, Rule


def get_config() -> KarabinerConfig:
    """Approximate a goku-style configuration using KarabinerPyX primitives."""
    config = KarabinerConfig()

    default_profile = Profile("Default profile")
    default_profile.add_device(
        vendor_id=1278,
        product_id=514,
        disable_built_in_keyboard_if_exists=True,
    )

    nav_rule = Rule("Map Left Option plus h/j/k/l to Arrows")
    for key, arrow in [
        ("h", "left_arrow"),
        ("j", "down_arrow"),
        ("k", "up_arrow"),
        ("l", "right_arrow"),
    ]:
        nav_rule.add(
            Manipulator(key)
            .modifiers(mandatory=["left_option"], optional=["any"])
            .to(arrow)
        )
    default_profile.add_rule(nav_rule)
    config.add_profile(default_profile)

    complex_profile = Profile("Complex Profile")
    complex_profile.set_parameters(
        **{
            "basic.simultaneous_threshold_milliseconds": 50,
            "basic.to_delayed_action_delay_milliseconds": 500,
            "basic.to_if_alone_timeout_milliseconds": 500,
            "basic.to_if_held_down_threshold_milliseconds": 500,
        }
    )

    excluded_apps = [
        "^org\\.gnu\\.Emacs$",
        "^com\\.apple\\.Terminal$",
        "^com\\.googlecode\\.iterm2$",
        "^io\\.alacritty$",
    ]

    complex_profile.add_rule(
        Rule("C+w to option+delete").add(
            Manipulator("w")
            .modifiers(mandatory=["left_control"])
            .to("delete_or_backspace", modifiers=["left_option"])
            .unless_app(excluded_apps)
        )
    )

    complex_profile.add_rule(
        Rule("caps lock to escape/control").add(
            Manipulator("caps_lock")
            .to("left_control")
            .if_alone("escape")
            .unless_variable("hhkhkbd", 1)
        )
    )

    w_mode = LayerStackBuilder("w_mode", "right_command")
    w_mode.map_combo(
        ["w", "i"],
        to_key=[
            {"set_variable": {"name": "w_mode", "value": 1}},
            {
                "shell_command": (
                    'osascript -e \'tell application "Keyboard Maestro Engine" '
                    'to do script "Raycast: Store"\''
                )
            },
        ],
        detect_key_down_uninterruptedly=True,
        key_down_order="strict",
        key_up_order="strict_inverse",
        to_after_key_up=[{"set_variable": {"name": "w_mode", "value": 0}}],
    )
    w_mode.map("i", "i")

    for rule in w_mode.build_rules():
        complex_profile.add_rule(rule)

    config.add_profile(complex_profile)
    return config


if __name__ == "__main__":
    config = get_config()
    print(config.to_json())
