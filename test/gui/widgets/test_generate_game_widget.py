from unittest.mock import MagicMock, AsyncMock

import pytest
from PySide6 import QtWidgets

from randovania.gui.widgets.generate_game_widget import GenerateGameWidget
from randovania.interface_common.options import Options
from randovania.layout.generator_parameters import GeneratorParameters
from randovania.layout.permalink import Permalink


@pytest.fixture(name="tab")
def _tab(skip_qtbot, preset_manager, game_enum):
    window_manager = MagicMock()
    window_manager.preset_manager = preset_manager

    widget = GenerateGameWidget()
    skip_qtbot.addWidget(widget)
    widget.setup_ui(game_enum, window_manager, MagicMock(), MagicMock())
    return widget


def test_add_new_preset(tab, preset_manager):
    preset = preset_manager.default_preset
    tab.create_preset_tree.select_preset = MagicMock()
    tab._window_manager.preset_manager = MagicMock()

    # Run
    tab._add_new_preset(preset)

    # Assert
    tab._window_manager.preset_manager.add_new_preset.assert_called_once_with(preset)
    tab.create_preset_tree.select_preset.assert_called_once_with(preset)


@pytest.mark.parametrize("has_existing_window", [False, True])
async def test_on_customize_button(tab, mocker, has_existing_window):
    mock_settings_window = mocker.patch("randovania.gui.widgets.generate_game_widget.CustomizePresetDialog")
    mock_execute_dialog = mocker.patch("randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock)
    mock_execute_dialog.return_value = QtWidgets.QDialog.Accepted
    tab._add_new_preset = MagicMock()
    tab._logic_settings_window = MagicMock() if has_existing_window else None
    tab.create_preset_tree = MagicMock()
    tab.create_preset_tree.selectedItems.return_value = [MagicMock()]

    # Run
    await tab._on_customize_preset()

    # Assert
    if has_existing_window:
        tab._logic_settings_window.raise_.assert_called_once_with()
        mock_settings_window.assert_not_called()
        mock_execute_dialog.assert_not_awaited()
        tab._add_new_preset.assert_not_called()
    else:
        mock_settings_window.assert_called_once()
        mock_execute_dialog.assert_awaited_once_with(mock_settings_window.return_value)
        tab._add_new_preset.assert_called_once()


@pytest.mark.parametrize("allow_experimental", [False, True])
def test_on_options_changed_select_preset(tab, is_dev_version, allow_experimental):
    preset = tab._window_manager.preset_manager.default_preset_for_game(tab.game)

    tab._options.experimental_games = allow_experimental
    tab._options.selected_preset_uuid = preset.uuid

    # Run
    tab.on_options_changed(tab._options)

    # Assert
    assert tab._current_preset_data == preset


def test_click_on_preset_tree(tab, skip_qtbot, tmp_path):
    preset = tab._window_manager.preset_manager.default_preset_for_game(tab.game)

    options = Options(tmp_path, None)
    options.on_options_changed = lambda: tab.on_options_changed(options)

    tab._options = options
    tab.on_options_changed(options)

    # Run
    item = tab.create_preset_tree.preset_to_item.get(preset.uuid)
    # assert item.parent().text(0) == "1"
    tab.create_preset_tree.selectionModel().reset()
    item.setSelected(True)

    # Assert
    assert tab._current_preset_data.get_preset() == preset.get_preset()


async def test_generate_new_seed(tab, mocker):
    # Setup
    mock_randint: MagicMock = mocker.patch("random.randint", return_value=12341234)

    tab.create_preset_tree = MagicMock()
    tab.create_preset_tree.current_preset_data = tab._window_manager.preset_manager.default_preset
    tab.generate_layout_from_permalink = AsyncMock()

    spoiler = MagicMock(spec=bool)
    retries = MagicMock(spec=int)

    # Run
    await tab.generate_new_layout(spoiler, retries)

    # Assert
    tab.generate_layout_from_permalink.assert_awaited_once_with(
        permalink=Permalink.from_parameters(
            GeneratorParameters(
                seed_number=12341234,
                spoiler=spoiler,
                presets=[tab._window_manager.preset_manager.default_preset.get_preset()],
            )
        ),
        retries=retries,
    )
    mock_randint.assert_called_once_with(0, 2 ** 31)
