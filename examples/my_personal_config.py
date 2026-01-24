from __future__ import annotations

from karabinerpyx import KarabinerConfig, Profile, Rule, Manipulator


def get_config() -> KarabinerConfig:
    """
    根据 requirements.md 构建的个性化 Karabiner 配置。
    
    包含功能：
    1. Option + HJKL 映射为 方向键
    2. Ctrl + F/B 映射为 左右方向键
    3. Ctrl + W 映射为 Option + Delete (删除单词)
    4. CapsLock 增强：单击为 Escape，长按为 Control
    5. 右 Command 增强：单击触发 Command + Tab (切换应用)
    6. 左 Command 增强：单击触发 Command + Space (搜索)
    7. 交换分号 (;) 和 冒号 (:)
    """
    config = KarabinerConfig()
    profile = Profile("Personalized Profile")

    # -------------------------------------------------------------------------
    # 1. Option + HJKL -> 方向键 (Vim 风格)
    # -------------------------------------------------------------------------
    hjkl_nav = Rule("1. Option + HJKL 导航映射")
    mappings = [
        ("h", "left_arrow"),
        ("j", "down_arrow"),
        ("k", "up_arrow"),
        ("l", "right_arrow"),
    ]
    for from_key, to_key in mappings:
        hjkl_nav.add(
            Manipulator(from_key)
            .modifiers(mandatory=["left_option"], optional=["any"])
            .to(to_key)
        )
    profile.add_rule(hjkl_nav)

    # -------------------------------------------------------------------------
    # 2. Ctrl + F/B -> 左右方向键
    # -------------------------------------------------------------------------
    fb_nav = Rule("2. Ctrl + F/B 左右导航")
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

    # -------------------------------------------------------------------------
    # 3. Ctrl + W -> Option + Delete (删除前一个单词)
    # -------------------------------------------------------------------------
    ctrl_w_delete = Rule("3. Ctrl + W 删除单词")
    ctrl_w_delete.add(
        Manipulator("w")
        .modifiers(mandatory=["left_control"], optional=["any"])
        .to("delete_or_backspace", modifiers=["left_option"])
    )
    profile.add_rule(ctrl_w_delete)

    # -------------------------------------------------------------------------
    # 4. CapsLock 增强：单击 Escape, 长按 Control
    # -------------------------------------------------------------------------
    caps_lock_enhanced = Rule("4. CapsLock 增强 (Escape/Control)")
    caps_lock_enhanced.add(
        Manipulator("caps_lock")
        .to("left_control")
        .if_alone("escape")
    )
    profile.add_rule(caps_lock_enhanced)

    # -------------------------------------------------------------------------
    # 5. 右 Command 单击 -> Command + Tab (切换应用)
    # -------------------------------------------------------------------------
    right_cmd_tab = Rule("5. 右 Command 单击映射 (Cmd+Tab)")
    right_cmd_tab.add(
        Manipulator("right_command")
        .to("right_command")
        .if_alone("tab", modifiers=["left_command"])
    )
    profile.add_rule(right_cmd_tab)

    # -------------------------------------------------------------------------
    # 6. 左 Command 单击 -> Command + Spacebar (搜索/输入法)
    # -------------------------------------------------------------------------
    left_cmd_search = Rule("6. 左 Command 单击映射 (Cmd+Space)")
    left_cmd_search.add(
        Manipulator("left_command")
        .to("left_command")
        .if_alone("spacebar", modifiers=["left_command"])
    )
    profile.add_rule(left_cmd_search)

    # -------------------------------------------------------------------------
    # 7. 交换分号 (;) 和 冒号 (:)
    # -------------------------------------------------------------------------
    swap_semicolon = Rule("7. 交换分号和冒号")
    # 直接按分号键 -> 输出冒号 (Shift + ;)
    swap_semicolon.add(
        Manipulator("semicolon")
        .modifiers(optional=["any"])
        .to("semicolon", modifiers=["left_shift"])
    )
    # 按住 Shift + 分号键 -> 输出原始分号
    swap_semicolon.add(
        Manipulator("semicolon")
        .modifiers(mandatory=["left_shift"], optional=["any"])
        .to("semicolon")
    )
    profile.add_rule(swap_semicolon)

    # 将所有配置添加到 Profile 中
    config.add_profile(profile)
    return config


if __name__ == "__main__":
    # 使用 CLI 加载此脚本时，会自动寻找 'config' 变量或 'get_config()' 函数
    config = get_config()
    
    # 运行此脚本时执行预览 (dry-run)
    print("🚀 正在生成符合 requirements.md 的配置预览：\n")
    config.save(dry_run=True)
    
    print("\n💡 提示: 使用 'kpyx apply examples/my_personal_config.py' 来正式应用此配置。")
