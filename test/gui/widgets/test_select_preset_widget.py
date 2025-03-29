from __future__ import annotations

import copy
import typing
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest
from PySide6 import QtCore, QtWidgets

from randovania.gui.widgets.select_preset_widget import SelectPresetWidget
from randovania.interface_common.options import Options
from randovania.layout.versioned_preset import VersionedPreset

if TYPE_CHECKING:
    import pytest_mock


@pytest.fixture
def widget(skip_qtbot, preset_manager, game_enum) -> SelectPresetWidget:
    window_manager = MagicMock()
    window_manager.preset_manager = preset_manager

    widget = SelectPresetWidget()
    skip_qtbot.addWidget(widget)
    widget.setup_ui(game_enum, window_manager, MagicMock())
    return widget


def test_add_new_preset(widget: SelectPresetWidget, preset_manager):
    preset = preset_manager.default_preset
    widget.create_preset_tree.select_preset = MagicMock()
    widget._window_manager = MagicMock()
    widget._window_manager.preset_manager = MagicMock()
    options = widget._options.__enter__.return_value

    # Run
    widget._add_new_preset(preset, parent=None)

    # Assert
    widget._window_manager.preset_manager.add_new_preset.assert_called_once_with(preset)
    widget.create_preset_tree.select_preset.assert_called_once_with(preset)
    options.set_parent_for_preset.assert_called_once_with(preset.uuid, None)
    options.set_selected_preset_uuid_for.assert_called_once_with(widget._game, preset.uuid)


@pytest.mark.parametrize("is_included_preset", [False, True])
@pytest.mark.parametrize("has_existing_window", [False, True])
async def test_on_customize_button(
    widget: SelectPresetWidget, mocker: pytest_mock.MockerFixture, has_existing_window, is_included_preset
):
    mock_settings_window = mocker.patch("randovania.gui.widgets.select_preset_widget.CustomizePresetDialog")
    mock_editor = mocker.patch("randovania.gui.widgets.select_preset_widget.PresetEditor")
    mock_execute_dialog = mocker.patch("randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock)
    mock_execute_dialog.return_value = QtWidgets.QDialog.DialogCode.Accepted
    widget._add_new_preset = MagicMock()
    widget._logic_settings_window = MagicMock() if has_existing_window else None
    widget._options.get_parent_for_preset = MagicMock()

    versioned_preset = MagicMock()
    versioned_preset.is_included_preset = is_included_preset
    old_preset = versioned_preset.get_preset.return_value
    widget.create_preset_tree = MagicMock()
    widget.create_preset_tree.current_preset_data = versioned_preset

    # Run
    await widget._on_customize_preset()

    # Assert
    if has_existing_window:
        widget._logic_settings_window.raise_.assert_called_once_with()
        mock_settings_window.assert_not_called()
        mock_execute_dialog.assert_not_awaited()
        widget._add_new_preset.assert_not_called()
    else:
        versioned_preset.get_preset.assert_called_once_with()

        if is_included_preset:
            parent_uuid = old_preset.uuid
            old_preset.fork.assert_called_once_with()
            old_preset = old_preset.fork.return_value
        else:
            widget._options.get_parent_for_preset.assert_called_once_with(old_preset.uuid)
            parent_uuid = widget._options.get_parent_for_preset.return_value

        mock_editor.assert_called_once_with(old_preset, widget._options)
        mock_settings_window.assert_called_once_with(widget._window_manager, mock_editor.return_value)
        mock_execute_dialog.assert_awaited_once_with(mock_settings_window.return_value)
        widget._add_new_preset.assert_called_once_with(
            VersionedPreset.with_preset(mock_editor.return_value.create_custom_preset_with.return_value),
            parent=parent_uuid,
        )


def test_on_options_changed_select_preset(widget: SelectPresetWidget, is_dev_version):
    preset = widget._window_manager.preset_manager.default_preset_for_game(widget._game)

    widget._options.selected_preset_uuid = preset.uuid

    # Run
    widget.on_options_changed(widget._options)

    # Assert
    assert widget._current_preset_data == preset


def test_click_on_preset_tree(widget: SelectPresetWidget, skip_qtbot, tmp_path):
    preset = widget._window_manager.preset_manager.default_preset_for_game(widget._game)

    options = Options(tmp_path, None)
    options.on_options_changed = lambda: widget.on_options_changed(options)

    widget._options = options
    widget.on_options_changed(options)

    # Run
    item = widget.create_preset_tree.preset_to_item.get(preset.uuid)
    # assert item.parent().text(0) == "1"
    widget.create_preset_tree.selectionModel().reset()
    item.setSelected(True)

    # Assert
    assert widget._current_preset_data.get_preset() == preset.get_preset()


@pytest.mark.parametrize("has_result", [False, True])
async def test_on_view_preset_history(widget: SelectPresetWidget, has_result, mocker: pytest_mock.MockerFixture):
    default_preset = widget._window_manager.preset_manager.default_preset
    widget.create_preset_tree = MagicMock()
    widget.create_preset_tree.current_preset_data = default_preset

    new_preset = VersionedPreset.with_preset(default_preset.get_preset().fork())

    mock_dialog = mocker.patch("randovania.gui.widgets.select_preset_widget.PresetHistoryDialog")
    mock_dialog.return_value.selected_preset.return_value = new_preset.get_preset() if has_result else None

    mock_execute_dialog = mocker.patch("randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock)
    mock_execute_dialog.return_value = (
        QtWidgets.QDialog.DialogCode.Accepted if has_result else QtWidgets.QDialog.DialogCode.Rejected
    )

    # Run
    await widget._on_view_preset_history()

    # Assert
    mock_execute_dialog.assert_awaited_once_with(mock_dialog.return_value)
    if has_result:
        assert widget._window_manager.preset_manager.custom_presets == {new_preset.uuid: new_preset}
    else:
        assert widget._window_manager.preset_manager.custom_presets == {}


def test_select_preset_incompatible_preset(
    widget: SelectPresetWidget, preset_manager, mocker: pytest_mock.MockerFixture
):
    mocker.patch("randovania.layout.preset.Preset.settings_incompatible_with_multiworld", return_value=["Foo", "Bar"])

    can_generate = MagicMock()
    widget.CanGenerate.connect(can_generate)

    widget.for_multiworld = True
    widget.on_preset_changed(preset=preset_manager.default_preset_for_game(widget._game))

    can_generate.assert_called_once_with(False)
    assert "The following settings are incompatible with multiworld" in widget.create_preset_description.text()


def test_on_tree_context_menu_on_item(widget: SelectPresetWidget):
    widget._preset_menu.exec = MagicMock()

    widget._on_tree_context_menu(QtCore.QPoint(0, 0))

    # Assert
    assert widget._preset_menu.action_customize.isEnabled()
    widget._preset_menu.exec.assert_called_once()


def test_on_tree_context_menu_on_nothing(widget: SelectPresetWidget):
    widget._preset_menu.exec = MagicMock()

    widget._on_tree_context_menu(QtCore.QPoint(0, 500))

    # Assert
    assert not widget._preset_menu.action_customize.isEnabled()
    widget._preset_menu.exec.assert_called_once()


def test_menu_set_preset_broken(widget: SelectPresetWidget):
    broken_data = copy.deepcopy(widget._window_manager.preset_manager.default_preset_for_game(widget._game).as_json)
    broken_data["schema_version"] = 6

    broken_preset = VersionedPreset(broken_data)
    widget._preset_menu.set_preset(broken_preset)

    menu = widget._preset_menu
    actions = [
        menu.action_delete,
        menu.action_history,
        menu.action_export,
        menu.action_customize,
        menu.action_duplicate,
        menu.action_map_tracker,
        menu.action_required_tricks,
    ]
    assert [p.isEnabled() for p in actions] == [
        True,
        True,
        False,
        False,
        False,
        False,
        False,
    ]


@pytest.mark.parametrize("confirm", [False, True])
def test_on_import_preset(widget: SelectPresetWidget, mocker: pytest_mock.MockerFixture, confirm: bool) -> None:
    mock_prompt = mocker.patch("randovania.gui.lib.common_qt_lib.prompt_user_for_preset_file")
    import_preset_file = typing.cast("MagicMock", widget._window_manager.import_preset_file)
    if not confirm:
        mock_prompt.return_value = None

    # Run
    widget._on_import_preset()

    # Assert
    mock_prompt.assert_called_once_with(widget._window_manager, new_file=False)
    if confirm:
        import_preset_file.assert_called_once_with(mock_prompt.return_value)
    else:
        import_preset_file.assert_not_called()
