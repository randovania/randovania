from unittest.mock import MagicMock, AsyncMock

import pytest
from PySide6 import QtWidgets

from randovania.gui.lib import async_dialog
from randovania.gui.widgets.generate_game_widget import GenerateGameWidget
from randovania.interface_common.options import Options
from randovania.layout.generator_parameters import GeneratorParameters
from randovania.layout.permalink import Permalink
from randovania.layout.versioned_preset import VersionedPreset


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


def test_on_options_changed_select_preset(tab, is_dev_version):
    preset = tab._window_manager.preset_manager.default_preset_for_game(tab.game)

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


@pytest.mark.parametrize(["has_unsupported", "abort_generate"], [
    (False, False),
    (True, False),
    (True, True),
])
async def test_generate_new_layout(tab, mocker, has_unsupported, abort_generate):
    # Setup
    mock_randint: MagicMock = mocker.patch("random.randint", return_value=12341234)
    mock_warning: AsyncMock = mocker.patch("randovania.gui.lib.async_dialog.warning")

    versioned_preset = MagicMock()
    versioned_preset.name = "PresetName"
    preset = versioned_preset.get_preset.return_value
    preset.configuration.unsupported_features.return_value = ["Unsup1", "Unsup2"] if has_unsupported else []

    mock_warning.return_value = async_dialog.StandardButton.No if abort_generate else async_dialog.StandardButton.Yes

    tab.create_preset_tree = MagicMock()
    tab.create_preset_tree.current_preset_data = versioned_preset
    tab.generate_layout_from_permalink = AsyncMock()

    spoiler = MagicMock(spec=bool)
    retries = MagicMock(spec=int)

    # Run
    await tab.generate_new_layout(spoiler, retries)

    # Assert
    if has_unsupported:
        mock_warning.assert_awaited_once_with(
            tab, "Unsupported Features",
            "Preset 'PresetName' uses the unsupported features:\nUnsup1, Unsup2\n\n"
            "Are you sure you want to continue?",
            buttons=async_dialog.StandardButton.Yes | async_dialog.StandardButton.No,
            default_button=async_dialog.StandardButton.No,
        )
    else:
        mock_warning.assert_not_awaited()

    if abort_generate:
        tab.generate_layout_from_permalink.assert_not_awaited()
        mock_randint.assert_not_called()
    else:
        tab.generate_layout_from_permalink.assert_awaited_once_with(
            permalink=Permalink.from_parameters(
                GeneratorParameters(
                    seed_number=12341234,
                    spoiler=spoiler,
                    presets=[preset],
                )
            ),
            retries=retries,
        )
        mock_randint.assert_called_once_with(0, 2 ** 31)


async def test_on_view_preset_history(tab, mocker):
    default_preset = tab._window_manager.preset_manager.default_preset
    tab.create_preset_tree = MagicMock()
    tab.create_preset_tree.current_preset_data = default_preset

    new_preset = VersionedPreset.with_preset(default_preset.get_preset().fork())

    mock_dialog = mocker.patch("randovania.gui.widgets.generate_game_widget.PresetHistoryDialog")
    mock_dialog.return_value.selected_preset.return_value = new_preset

    mock_execute_dialog = mocker.patch("randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock)
    mock_execute_dialog.return_value = QtWidgets.QDialog.Accepted

    # Run
    await tab._on_view_preset_history()

    # Assert
    mock_execute_dialog.assert_awaited_once_with(mock_dialog.return_value)
    assert new_preset.uuid in tab._window_manager.preset_manager.custom_presets
