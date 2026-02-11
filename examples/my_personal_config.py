from __future__ import annotations

from karabinerpyx import KarabinerConfig, Manipulator, Profile, Rule


def get_config() -> KarabinerConfig:
    """Build personalized configuration from requirements.md."""
    config = KarabinerConfig()
    profile = Profile("Personalized Profile from KarabinerPyX")

    hjkl_nav = Rule("1. Option + HJKL navigation")
    for from_key, to_key in [
        ("h", "left_arrow"),
        ("j", "down_arrow"),
        ("k", "up_arrow"),
        ("l", "right_arrow"),
    ]:
        hjkl_nav.add(
            Manipulator(from_key)
            .modifiers(mandatory=["left_option"], optional=["any"])
            .to(to_key)
        )
    profile.add_rule(hjkl_nav)

    fb_nav = Rule("2. Ctrl + F/B navigation")
    fb_nav.add(
        Manipulator("f")
        .modifiers(mandatory=["left_control"], optional=["any"])
        .to("right_arrow")
    )
    fb_nav.add(
        Manipulator("b")
        .modifiers(mandatory=["left_control"], optional=["any"])
        .to("left_arrow")
    )
    profile.add_rule(fb_nav)

    ctrl_w_delete = Rule("3. Ctrl + W delete previous word")
    ctrl_w_delete.add(
        Manipulator("w")
        .modifiers(mandatory=["left_control"], optional=["any"])
        .to("delete_or_backspace", modifiers=["left_option"])
    )
    profile.add_rule(ctrl_w_delete)

    profile.add_rule(
        Rule("4. CapsLock as Escape/Control").add(
            Manipulator("caps_lock").to("left_control").if_alone("escape")
        )
    )

    profile.add_rule(
        Rule("5. Right Command tap to Cmd+Tab").add(
            Manipulator("right_command")
            .to("right_command")
            .if_alone("tab", modifiers=["left_command"])
        )
    )

    profile.add_rule(
        Rule("6. Left Command tap to Cmd+Space").add(
            Manipulator("left_command")
            .to("left_command")
            .if_alone("spacebar", modifiers=["left_command"])
        )
    )

    swap_semicolon = Rule("7. Swap semicolon and colon")
    swap_semicolon.add(
        Manipulator("semicolon")
        .modifiers(optional=["any"])
        .to("semicolon", modifiers=["left_shift"])
    )
    swap_semicolon.add(
        Manipulator("semicolon")
        .modifiers(mandatory=["left_shift"], optional=["any"])
        .to("semicolon")
    )
    profile.add_rule(swap_semicolon)

    config.add_profile(profile)
    return config


if __name__ == "__main__":
    config = get_config()
    print("Generating preview config from requirements.md")
    config.save(dry_run=True)
