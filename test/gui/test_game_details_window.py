import collections
import dataclasses

from PySide6 import QtWidgets, QtCore
from mock import MagicMock, AsyncMock, call, ANY

from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.prime3.layout.corruption_cosmetic_patches import CorruptionCosmeticPatches
from randovania.gui.game_details.game_details_window import GameDetailsWindow
from randovania.gui.game_details.pickup_details_tab import PickupDetailsTab
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.layout.generator_parameters import GeneratorParameters
from randovania.layout.layout_description import LayoutDescription


async def test_export_iso(skip_qtbot, mocker):
    # Setup
    mock_execute_dialog = mocker.patch("randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock,
                                       return_value=QtWidgets.QDialog.Accepted)

    options = MagicMock()
    options.output_directory = None

    window_manager = MagicMock()

    window = GameDetailsWindow(window_manager, options)
    skip_qtbot.addWidget(window)
    window.layout_description = MagicMock()
    window._player_names = {}
    game = window.layout_description.get_preset.return_value.game
    game.exporter.is_busy = False
    window.layout_description.all_games = [game]
    patch_data = game.patch_data_factory.return_value.create_data.return_value

    players_config = PlayersConfiguration(
        player_index=window.current_player_index,
        player_names=window._player_names,
    )

    # Run
    await window._export_iso()

    # Assert
    game.patch_data_factory.assert_called_once_with(
        window.layout_description,
        players_config,
        options.options_for_game.return_value.cosmetic_patches
    )
    game.gui.export_dialog.assert_called_once_with(
        options,
        patch_data,
        window.layout_description.shareable_word_hash,
        window.layout_description.has_spoiler,
        [game]
    )
    mock_execute_dialog.assert_awaited_once_with(game.gui.export_dialog.return_value)
    game.exporter.export_game.assert_called_once_with(
        patch_data,
        game.gui.export_dialog.return_value.get_game_export_params.return_value,
        progress_update=ANY,
    )


def test_update_layout_description_no_spoiler(skip_qtbot, mocker):
    # Setup
    mock_describer = mocker.patch("randovania.layout.preset_describer.describe", return_value=["a", "b", "c", "d"])
    mock_merge = mocker.patch("randovania.layout.preset_describer.merge_categories", return_value="<description>")

    options = MagicMock()
    description = MagicMock(spec=LayoutDescription)
    description.player_count = 1
    description.shareable_hash = "12345"
    description.shareable_word_hash = "Some Hash Words"
    description.randovania_version_text = "v1.2.4"
    description.permalink.as_base64_str = "<permalink>"
    description.generator_parameters = MagicMock(spec=GeneratorParameters)
    description.has_spoiler = False

    preset = description.get_preset.return_value
    preset.game.data.layout.get_ingame_hash.return_value = "<image>"
    preset.name = "CustomPreset"

    window = GameDetailsWindow(None, options)
    skip_qtbot.addWidget(window)

    # Run
    window.update_layout_description(description)

    # Assert
    mock_describer.assert_called_once_with(preset)
    mock_merge.assert_has_calls([
        call(["a", "c"]),
        call(["b", "d"]),
    ])
    assert window.layout_title_label.text() == ("""
        <p>
            Generated with Randovania v1.2.4<br />
            Seed Hash: Some Hash Words (12345)<br/>
            In-game Hash: <image><br/>
            Preset Name: CustomPreset
        </p>
        """)


def test_update_layout_description_actual_seed(skip_qtbot, test_files_dir):
    description = LayoutDescription.from_file(test_files_dir.joinpath("log_files", "seed_a.rdvgame"))

    # Run
    window = GameDetailsWindow(None, MagicMock())
    skip_qtbot.addWidget(window)
    window.update_layout_description(description)

    # Assert
    pickup_details_tab = window._game_details_tabs[0]
    assert isinstance(pickup_details_tab, PickupDetailsTab)
    assert len(pickup_details_tab.pickup_spoiler_buttons) == 119
    assert pickup_details_tab.pickup_spoiler_show_all_button.text() == "Show All"
    skip_qtbot.mouseClick(pickup_details_tab.pickup_spoiler_show_all_button, QtCore.Qt.LeftButton)
    assert pickup_details_tab.pickup_spoiler_show_all_button.text() == "Hide All"


async def test_show_dialog_for_prime3_layout(skip_qtbot, mocker, corruption_game_description, empty_patches):
    mock_execute_dialog = mocker.patch("randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock)
    mock_clipboard: MagicMock = mocker.patch("randovania.gui.lib.common_qt_lib.set_clipboard")

    options = MagicMock()
    options.options_for_game.return_value.cosmetic_patches = CorruptionCosmeticPatches()
    window = GameDetailsWindow(None, options)
    window.player_index_combo.addItem("Current", 0)
    skip_qtbot.addWidget(window)

    target = MagicMock()
    target.pickup.name = "Boost Ball"

    patches = dataclasses.replace(empty_patches, starting_location=corruption_game_description.starting_location)
    for i in range(100):
        patches.pickup_assignment[PickupIndex(i)] = target

    window.layout_description = MagicMock()
    window.layout_description.all_patches = {0: patches}

    # Run
    await window._show_dialog_for_prime3_layout()

    # Assert
    mock_execute_dialog.assert_awaited_once()
    mock_clipboard.assert_called_once()
