"""KarabinerPyX - A Python DSL for Karabiner-Elements Configuration."""

from karabinerpyx.models import (
    KarabinerConfig,
    Manipulator,
    Profile,
    Rule,
)
from karabinerpyx.layer import (
    LayerStackBuilder,
    SimultaneousManipulator,
)
from karabinerpyx.templates import (
    MACRO_TEMPLATES,
    make_shell_command,
)
from karabinerpyx.deploy import (
    backup_config,
    reload_karabiner,
    save_config,
    validate_json,
)
from karabinerpyx.keys import (
    CMD,
    ALT,
    OPT,
    CTRL,
    SHIFT,
    R_CMD,
    L_CMD,
    R_ALT,
    L_ALT,
    R_OPT,
    L_OPT,
    R_CTRL,
    L_CTRL,
    R_SHIFT,
    L_SHIFT,
    CAPS,
    ESC,
    RET,
    ENTER,
    SPC,
    TAB,
    BS,
    DEL,
    UP,
    DOWN,
    LEFT,
    RIGHT,
    PGUP,
    PGDN,
    HOME,
    END,
)

__version__ = "0.1.0"

__all__ = [
    # Core models
    "KarabinerConfig",
    "Manipulator",
    "Profile",
    "Rule",
    # Layer system
    "LayerStackBuilder",
    "SimultaneousManipulator",
    # Templates
    "MACRO_TEMPLATES",
    "make_shell_command",
    # Deployment
    "backup_config",
    "reload_karabiner",
    "save_config",
    "validate_json",
    # Keys
    "CMD",
    "ALT",
    "OPT",
    "CTRL",
    "SHIFT",
    "R_CMD",
    "L_CMD",
    "R_ALT",
    "L_ALT",
    "R_OPT",
    "L_OPT",
    "R_CTRL",
    "L_CTRL",
    "R_SHIFT",
    "L_SHIFT",
    "CAPS",
    "ESC",
    "RET",
    "ENTER",
    "SPC",
    "TAB",
    "BS",
    "DEL",
    "UP",
    "DOWN",
    "LEFT",
    "RIGHT",
    "PGUP",
    "PGDN",
    "HOME",
    "END",
]
