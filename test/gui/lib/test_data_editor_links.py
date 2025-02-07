from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from PySide6.QtWidgets import QWidget

from randovania.game.game_enum import RandovaniaGame
from randovania.game_description.db.area_identifier import AreaIdentifier
from randovania.gui.lib.data_editor_links import (
    data_editor_href,
    get_human_readable_region_and_area,
    on_click_data_editor_link,
)


@pytest.mark.parametrize("trick_levels", [None, MagicMock()])
def test_click_on_link(skip_qtbot, trick_levels):
    # Setup
    main_window = QWidget()
    main_window.open_data_visualizer_at = MagicMock()
    skip_qtbot.add_widget(main_window)
    world_name = "World"
    area_name = "Area"

    # Run
    signal_handler = on_click_data_editor_link(main_window, RandovaniaGame.BLANK, trick_levels)
    signal_handler(f"data-editor://{world_name}/{area_name}")

    # Assert
    main_window.open_data_visualizer_at.assert_called_once_with(
        world_name,
        area_name,
        game=RandovaniaGame.BLANK,
        trick_levels=trick_levels,
    )


@pytest.mark.parametrize("text", [None, "Some random text"])
@pytest.mark.parametrize(
    "area_id",
    [
        AreaIdentifier("Agon Wastes", "Agon Temple"),
        AreaIdentifier("Agon Wastes", "Dark Agon Temple"),
    ],
)
def test_data_editor_href(echoes_game_description, text: str | None, area_id: AreaIdentifier):
    # Setup
    region, area = echoes_game_description.region_list.region_and_area_by_area_identifier(area_id)
    if text is None:
        text = get_human_readable_region_and_area(region, area)

    # Run
    url = data_editor_href(region, area, text)

    # Assert
    assert url == f'<a href="data-editor://{region.correct_name(area.in_dark_aether)}/{area.name}">{text}</a>'
