from __future__ import annotations

from karabinerpyx import KarabinerConfig, Profile, Rule, Manipulator, LayerStackBuilder

def get_config() -> KarabinerConfig:
    config = KarabinerConfig()

    # =========================================================================
    # Profile 1: Default profile
    # =========================================================================
    p1 = Profile("Default profile")
    p1.add_device(
        vendor_id=1278,
        product_id=514,
        disable_built_in_keyboard_if_exists=True
    )
    
    # Map Left Option plus h/j/k/l to Arrows
    nav_rule = Rule("Map Left Option plus h/j/k/l to Arrows")
    for key, arrow in [("h", "left_arrow"), ("j", "down_arrow"), ("k", "up_arrow"), ("l", "right_arrow")]:
        nav_rule.add(
            Manipulator(key)
            .modifiers(mandatory=["left_option"], optional=["any"])
            .to(arrow)
        )
    # Note: Manipulator class currently doesn't have a clean way to set mandatory/optional modifiers 
    # except via add_dict or if I enhance it. Let's use add_dict for now.
    
    p1.add_rule(nav_rule)
    config.add_profile(p1)

    # =========================================================================
    # Profile 2: Complex Profile (Simulating the rest of goku.json)
    # =========================================================================
    p2 = Profile("Complex Profile")
    p2.set_parameters(**{
        "basic.simultaneous_threshold_milliseconds": 50,
        "basic.to_delayed_action_delay_milliseconds": 500,
        "basic.to_if_alone_timeout_milliseconds": 500,
        "basic.to_if_held_down_threshold_milliseconds": 500
    })

    # Rule: C+w to option+delete (excluding terminals/emacs)
    excluded_apps = [
        "^org\\.gnu\\.Emacs$", "^dev\\.warp\\.Warp-Stable$", "com\\.hogbaysoftware\\.Bike-setapp",
        "^org\\.gnu\\.AquamacsEmacs$", "^org\\.gnu\\.Aquamacs$", "^com\\.apple\\.Terminal$",
        "^com\\.googlecode\\.iterm2$", "^co\\.zeit\\.hyperterm$", "^co\\.zeit\\.hyper$",
        "^io\\.alacritty$", "^com\\.github\\.wez\\.wezterm$", "^net\\.kovidgoyal\\.kitty$"
    ]
    p2.add_rule(
        Rule("C+w to option+delete")
        .add(
            Manipulator("w")
            .modifiers(mandatory=["left_control"])
            .to("delete_or_backspace", modifiers=["left_option"])
            .unless_app(excluded_apps)
        )
    )

    # Rule: caps lock -> escape(alone) and caps lock -> control
    p2.add_rule(
        Rule("caps lock -> escape(alone) and caps lock -> control")
        .add(
            Manipulator("caps_lock")
            .to("left_control")
            .if_alone("escape")
            .unless_variable("hhkhkbd", 1)
        )
    )

    # Rule: w-mode (Simultaneous)
    w_mode = LayerStackBuilder("w-mode", []) # Dummy trigger, we'll use map_combo manually
    w_mode.map_combo(
        ["w", "i"],
        to_key=[
            {"set_variable": {"name": "w-mode", "value": 1}},
            {"shell_command": "osascript -e 'tell application \"Keyboard Maestro Engine\" to do script \"Raycast: Store\"'"}
        ],
        detect_key_down_uninterruptedly=True,
        key_down_order="strict",
        key_up_order="strict_inverse",
        to_after_key_up=[{"set_variable": {"name": "w-mode", "value": 0}}]
    )
    # Add an action inside w-mode
    w_mode.map("i", "i") # Placeholder
    
    for rule in w_mode.build_rules():
        # Clean up description to match goku if needed
        p2.add_rule(rule)

    config.add_profile(p2)
    return config

if __name__ == "__main__":
    config = get_config()
    print(config.to_json())
