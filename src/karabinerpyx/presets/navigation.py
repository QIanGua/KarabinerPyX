from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from karabinerpyx.layer import LayerStackBuilder


def vim_navigation(builder: LayerStackBuilder) -> LayerStackBuilder:
    """Add Vim-style navigation mappings to a layer."""
    return (
        builder.map("h", "left_arrow")
        .map("j", "down_arrow")
        .map("k", "up_arrow")
        .map("l", "right_arrow")
        .map("u", "page_up")
        .map("d", "page_down")
        .map("0", "home")
        .map("4", "end")
    )
