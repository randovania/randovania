from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from PySide6.QtWidgets import QWidget

from randovania.game_description.resources.trick_resource_info import TrickResourceInfo
from randovania.games.game import RandovaniaGame
from randovania.gui.dialog import trick_details_popup
from randovania.layout.base.trick_level import LayoutTrickLevel


@pytest.mark.parametrize("trick_levels", [None, MagicMock()])
def test_click_on_link(echoes_game_description, skip_qtbot, trick_levels):
    # Setup
    main_window = QWidget()
    main_window.open_data_visualizer_at = MagicMock()
    skip_qtbot.add_widget(main_window)
    world_name = "World"
    area_name = "Area"

    # Run
    popup = trick_details_popup.TrickDetailsPopup(
        main_window,
        main_window,
        echoes_game_description,
        TrickResourceInfo(1234, "Nothing", "Nothing", "Some description!"),
        LayoutTrickLevel.EXPERT,
        trick_levels,
    )
    popup._on_click_link_to_data_editor(f"data-editor://{world_name}/{area_name}")

    # Assert
    main_window.open_data_visualizer_at.assert_called_once_with(
        world_name,
        area_name,
        game=RandovaniaGame.METROID_PRIME_ECHOES,
        trick_levels=trick_levels,
    )
