from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from karabinerpyx.layer import LayerStackBuilder


def vim_navigation(builder: LayerStackBuilder) -> LayerStackBuilder:
    """Add Vim-style navigation mappings (HJKL to Arrows) to a layer.

    Mappings:
        h -> left_arrow
        j -> down_arrow
        k -> up_arrow
        l -> right_arrow
        u -> page_up
        d -> page_down
        0 -> home
        $ -> end (mapped to semicolon as a proxy for $)

    Args:
        builder: The LayerStackBuilder to add mappings to.

    Returns:
        The updated LayerStackBuilder.
    """
    return (
        builder.map("h", "left_arrow")
        .map("j", "down_arrow")
        .map("k", "up_arrow")
        .map("l", "right_arrow")
        .map("u", "page_up")
        .map("d", "page_down")
        .map("0", "home")
        .map(
            "4", "end"
        )  # $ is usually shift+4, so 4 is a reasonable choice if shift is optional
    )
