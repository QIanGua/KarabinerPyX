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
]
