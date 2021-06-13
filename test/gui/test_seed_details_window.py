import collections

import pytest
from PySide2 import QtWidgets, QtCore
from mock import MagicMock, AsyncMock, call, ANY

from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.gui.seed_details_window import SeedDetailsWindow
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.layout.layout_description import LayoutDescription
from randovania.layout.prime3.corruption_cosmetic_patches import CorruptionCosmeticPatches


@pytest.mark.asyncio
async def test_export_iso(skip_qtbot, mocker):
    # Setup
    mock_input_dialog = mocker.patch("randovania.gui.seed_details_window.GameInputDialog")
    mock_execute_dialog = mocker.patch("randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock,
                                       return_value=QtWidgets.QDialog.Accepted)

    options = MagicMock()
    options.output_directory = None

    window_manager = MagicMock()
    patcher_provider = window_manager.patcher_provider
    patcher = patcher_provider.patcher_for_game.return_value
    patcher.is_busy = False

    window = SeedDetailsWindow(window_manager, options)
    window.layout_description = MagicMock()
    window._player_names = {}

    players_config = PlayersConfiguration(
        player_index=window.current_player_index,
        player_names=window._player_names,
    )

    # Run
    await window._export_iso()

    # Assert
    mock_execute_dialog.assert_awaited_once()
    patcher.create_patch_data.assert_called_once_with(window.layout_description, players_config,
                                                      options.options_for_game.return_value.cosmetic_patches)
    patcher.patch_game.assert_called_once_with(
        mock_input_dialog.return_value.input_file,
        mock_input_dialog.return_value.output_file,
        patcher.create_patch_data.return_value,
        window._options.internal_copies_path,
        progress_update=ANY,
    )


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

    options = MagicMock()
    options.options_for_game.return_value.cosmetic_patches = CorruptionCosmeticPatches()
    window = SeedDetailsWindow(None, options)
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
