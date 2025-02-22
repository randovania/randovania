from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from PySide6.QtWidgets import QWidget

from randovania.game_description.resources.trick_resource_info import TrickResourceInfo
from randovania.gui.dialog import trick_details_popup
from randovania.layout.base.trick_level import LayoutTrickLevel


@pytest.mark.parametrize("trick_levels", [None, MagicMock()])
def test_create(echoes_game_description, skip_qtbot, trick_levels):
    # Setup
    main_window = QWidget()
    main_window.open_data_visualizer_at = MagicMock()
    skip_qtbot.add_widget(main_window)

    # Run
    popup = trick_details_popup.TrickDetailsPopup(
        main_window,
        main_window,
        echoes_game_description,
        TrickResourceInfo(1234, "Nothing", "Nothing", "Some description!"),
        LayoutTrickLevel.EXPERT,
        trick_levels,
    )

    # Assert
    assert popup.area_list_label.text() == "This trick is not used in this level."
