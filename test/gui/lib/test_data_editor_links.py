from __future__ import annotations

import urllib.parse
from unittest.mock import MagicMock

import pytest
from PySide6.QtWidgets import QWidget

from randovania.game.game_enum import RandovaniaGame
from randovania.game_description import default_database
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
    area_name = "Area (!@#$%^&*())"  # so many special characters!

    q = urllib.parse.quote

    # Run
    signal_handler = on_click_data_editor_link(main_window, RandovaniaGame.BLANK, trick_levels)
    signal_handler(f"data-editor://{q(world_name)}/{q(area_name)}")

    # Assert
    main_window.open_data_visualizer_at.assert_called_once_with(
        world_name,
        area_name,
        game=RandovaniaGame.BLANK,
        trick_levels=trick_levels,
    )


@pytest.mark.parametrize("text", [None, "Some random text"])
@pytest.mark.parametrize(
    ("game", "area_id"),
    [
        (RandovaniaGame.METROID_PRIME_ECHOES, AreaIdentifier("Agon Wastes", "Agon Temple")),
        (RandovaniaGame.METROID_PRIME_ECHOES, AreaIdentifier("Dark Agon Wastes", "Dark Agon Temple")),
        (RandovaniaGame.FUSION, AreaIdentifier("Sector 1 (SRX)", "Ridley Arena")),
    ],
)
def test_data_editor_href(text: str | None, game: RandovaniaGame, area_id: AreaIdentifier):
    # Setup
    description = default_database.game_description_for(game)
    region, area = description.region_list.region_and_area_by_area_identifier(area_id)
    if text is None:
        text = get_human_readable_region_and_area(region, area)

    q = urllib.parse.quote

    # Run
    url = data_editor_href(region, area, text)

    # Assert
    assert url == f'<a href="data-editor://{q(region.name)}/{q(area.name)}">{text}</a>'
