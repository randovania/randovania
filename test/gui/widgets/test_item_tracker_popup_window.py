from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

from PySide6 import QtWidgets

from randovania.game_description.resources.inventory import Inventory
from randovania.gui.widgets.item_tracker_popup_window import ItemTrackerPopupWindow

if TYPE_CHECKING:
    import pytest_mock


def test_change_tracker_layout(skip_qtbot, mocker: pytest_mock.MockerFixture, tmp_path):
    result = QtWidgets.QWidget()
    result.update_state = MagicMock()
    result.current_state = [5, 7]
    skip_qtbot.addWidget(result)

    mock_tracker = mocker.patch(
        "randovania.gui.widgets.item_tracker_popup_window.ItemTrackerWidget", return_value=result
    )
    on_close = MagicMock()

    p1 = tmp_path.joinpath("p1.json")
    p2 = tmp_path.joinpath("p2.json")
    p1.write_text("[1]")
    p2.write_text("[2]")

    themes = {
        "ThemeA": p1,
        "ThemeB": p2,
    }
    popup = ItemTrackerPopupWindow("Hello", themes, on_close)
    skip_qtbot.addWidget(popup)

    mock_tracker.assert_called_once_with([1])
    result.update_state.assert_called_once_with(Inventory.empty())

    popup._on_select_theme(p2)
    mock_tracker.assert_called_with([2])
    result.update_state.assert_called_with([5, 7])

    popup.close()
    on_close.assert_called_with()
