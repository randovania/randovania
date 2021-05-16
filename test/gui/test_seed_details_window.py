import collections

import pytest
from PySide2 import QtWidgets, QtCore
from mock import MagicMock, AsyncMock, call

from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.gui.seed_details_window import SeedDetailsWindow
from randovania.layout.layout_description import LayoutDescription


@pytest.mark.asyncio
async def test_export_iso(skip_qtbot, mocker):
    # Setup
    mock_execute_dialog = mocker.patch("randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock,
                                       return_value=QtWidgets.QDialog.Accepted)

    options = MagicMock()
    options.output_directory = None

    window = SeedDetailsWindow(None, options)
    window.layout_description = MagicMock()
    window._player_names = {}
    window.run_in_background_async = AsyncMock()

    # Run
    await window._export_iso()

    # Assert
    mock_execute_dialog.assert_awaited_once()
    window.run_in_background_async.assert_awaited_once()


def test_update_layout_description_no_spoiler(skip_qtbot, mocker):
    # Setup
    mock_describer = mocker.patch("randovania.gui.lib.preset_describer.describe", return_value=["a", "b", "c", "d"])
    mock_merge = mocker.patch("randovania.gui.lib.preset_describer.merge_categories", return_value="<description>")

    options = MagicMock()
    description = MagicMock()
    description.permalink.player_count = 1
    description.permalink.as_base64_str = "<permalink>"
    description.permalink.spoiler = False

    window = SeedDetailsWindow(None, options)
    skip_qtbot.addWidget(window)

    # Run
    window.update_layout_description(description)

    # Assert
    mock_describer.assert_called_once_with(description.permalink.get_preset.return_value)
    mock_merge.assert_has_calls([
        call(["a", "c"]),
        call(["b", "d"]),
    ])


def test_update_layout_description_actual_seed(skip_qtbot, test_files_dir):
    description = LayoutDescription.from_file(test_files_dir.joinpath("log_files", "seed_a.rdvgame"))

    # Run
    window = SeedDetailsWindow(None, MagicMock())
    skip_qtbot.addWidget(window)
    window.update_layout_description(description)

    # Assert
    assert len(window.pickup_spoiler_buttons) == 119
    assert window.pickup_spoiler_show_all_button.text() == "Show All"
    skip_qtbot.mouseClick(window.pickup_spoiler_show_all_button, QtCore.Qt.LeftButton)
    assert window.pickup_spoiler_show_all_button.text() == "Hide All"


@pytest.mark.asyncio
async def test_show_dialog_for_prime3_layout(skip_qtbot, mocker, corruption_game_description):
    mock_execute_dialog = mocker.patch("randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock)
    mock_clipboard: MagicMock = mocker.patch("PySide2.QtWidgets.QApplication.clipboard")

    window = SeedDetailsWindow(None, MagicMock())
    window.player_index_combo.addItem("Current", 0)
    skip_qtbot.addWidget(window)

    collections.namedtuple("MockPickup", ["name"])
    target = MagicMock()
    target.pickup.name = "Boost Ball"

    patches = corruption_game_description.create_game_patches()
    for i in range(100):
        patches.pickup_assignment[PickupIndex(i)] = target

    window.layout_description = MagicMock()
    window.layout_description.all_patches = {0: patches}

    # Run
    await window._show_dialog_for_prime3_layout()

    # Assert
    mock_execute_dialog.assert_awaited_once()
    mock_clipboard.return_value.setText.assert_called_once()
