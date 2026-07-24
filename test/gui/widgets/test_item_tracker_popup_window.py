from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

from PySide6 import QtWidgets

from randovania.game_description.resources.inventory import Inventory
from randovania.gui.item_tracker.item_tracker_popup_window import ItemTrackerPopupWindow
from randovania.gui.item_tracker.tracker_assets import TrackerAssetPaths

if TYPE_CHECKING:
    import pytest_mock


def test_change_tracker_layout(skip_qtbot, mocker: pytest_mock.MockerFixture, tmp_path):
    result = QtWidgets.QWidget()
    result.update_state = MagicMock()
    result.current_state = [5, 7]
    skip_qtbot.addWidget(result)

    mock_tracker = mocker.patch(
        "randovania.gui.item_tracker.item_tracker_popup_window.ItemTrackerWidget", return_value=result
    )
    mocker.patch.object(TrackerAssetPaths, "load", side_effect=[(1, 2), (3, 4)])
    on_close = MagicMock()

    paths_a = TrackerAssetPaths(tmp_path.joinpath("a-structure.json"), tmp_path.joinpath("a-theme.json"), tmp_path)
    paths_b = TrackerAssetPaths(tmp_path.joinpath("b-structure.json"), tmp_path.joinpath("b-theme.json"), tmp_path)

    trackers = {
        "ThemeA": paths_a,
        "ThemeB": paths_b,
    }
    popup = ItemTrackerPopupWindow("Hello", trackers, on_close)
    skip_qtbot.addWidget(popup)

    mock_tracker.assert_called_once_with(1, 2, tmp_path)
    result.update_state.assert_called_once_with(Inventory.empty())

    popup._on_select_theme(paths_b)
    mock_tracker.assert_called_with(3, 4, tmp_path)
    result.update_state.assert_called_with([5, 7])

    popup.close()
    on_close.assert_called_with()
