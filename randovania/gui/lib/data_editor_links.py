from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from randovania.game.game_enum import RandovaniaGame
    from randovania.game_description.db.area import Area
    from randovania.game_description.db.region import Region
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.layout.base.trick_level_configuration import TrickLevelConfiguration


def on_click_data_editor_link(
    window_manager: WindowManager, game: RandovaniaGame, trick_levels: TrickLevelConfiguration | None = None
) -> Callable[[str], None]:
    """
    Returns a callable that can be attached to a Label's `linkActivated` signal
    which opens the Data Editor to the region and area indicated in the URL.

    If `trick_levels` is provided, the data editor will automatically set its trick filters accordingly.
    """

    link_pattern = re.compile(r"^data-editor://([^)]+)/([^)]+)$")

    def inner(link: str) -> None:
        info = link_pattern.match(link)
        if info:
            region_name, area_name = info.group(1, 2)
            window_manager.open_data_visualizer_at(
                region_name,
                area_name,
                game=game,
                trick_levels=trick_levels,
            )

    return inner


def data_editor_href(region: Region, area: Area, text: str | None = None) -> str:
    """
    Creates a clickable data editor link for the given Region and Area.

    If text is not provided, a default of "Region - Area" is used.
    """

    if text is None:
        text = get_human_readable_region_and_area(region, area)
    return f'<a href="data-editor://{region.correct_name(area.in_dark_aether)}/{area.name}">{text}</a>'


def get_human_readable_region_and_area(region: Region, area: Area) -> str:
    return f"{region.correct_name(area.in_dark_aether)} - {area.name}"
