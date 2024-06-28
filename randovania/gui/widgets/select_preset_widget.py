from __future__ import annotations

import dataclasses
import json
import logging
import re
import traceback
import uuid
from typing import TYPE_CHECKING

import markdown
from PySide6 import QtCore, QtGui, QtWidgets
from qasync import asyncSlot

from randovania import monitoring
from randovania.gui.dialog.preset_history_dialog import PresetHistoryDialog
from randovania.gui.generated.select_preset_widget_ui import Ui_SelectPresetWidget
from randovania.gui.lib import async_dialog, common_qt_lib
from randovania.gui.preset_settings.customize_preset_dialog import CustomizePresetDialog
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout import preset_describer
from randovania.layout.versioned_preset import InvalidPreset, VersionedPreset
from randovania.lib.migration_lib import UnsupportedVersion

if TYPE_CHECKING:
    from pathlib import Path

    from randovania.games.game import RandovaniaGame
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.options import Options


class PresetMenu(QtWidgets.QMenu):
    action_customize: QtGui.QAction
    action_delete: QtGui.QAction
    action_history: QtGui.QAction
    action_export: QtGui.QAction
    action_duplicate: QtGui.QAction
    action_map_tracker: QtGui.QAction
    action_required_tricks: QtGui.QAction

    action_import: QtGui.QAction
    action_view_deleted: QtGui.QAction

    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)
        self.action_customize = QtGui.QAction(parent)
        self.action_delete = QtGui.QAction(parent)
        self.action_history = QtGui.QAction(parent)
        self.action_export = QtGui.QAction(parent)
        self.action_duplicate = QtGui.QAction(parent)
        self.action_map_tracker = QtGui.QAction(parent)
        self.action_required_tricks = QtGui.QAction(parent)
        self.action_import = QtGui.QAction(parent)
        self.action_view_deleted = QtGui.QAction(parent)

        self.action_customize.setText("Customize")
        self.action_delete.setText("Delete")
        self.action_history.setText("View previous versions")
        self.action_export.setText("Export")
        self.action_duplicate.setText("Duplicate")
        self.action_map_tracker.setText("Open map tracker")
        self.action_required_tricks.setText("View expected trick usage")
        self.action_import.setText("Import")
        self.action_view_deleted.setText("View deleted presets")

        self.addAction(self.action_customize)
        self.addAction(self.action_delete)
        self.addAction(self.action_history)
        self.addAction(self.action_export)
        self.addAction(self.action_duplicate)
        self.addAction(self.action_map_tracker)
        self.addAction(self.action_required_tricks)
        self.addSeparator()
        self.addAction(self.action_import)
        self.addAction(self.action_view_deleted)

        # TODO: Hide the ones that aren't implemented
        self.action_view_deleted.setVisible(False)

    def set_preset(self, preset: VersionedPreset | None):
        has_any_preset = preset is not None
        has_valid_preset = has_any_preset
        try:
            if preset is not None:
                preset.get_preset()
        except InvalidPreset:
            has_valid_preset = False

        for p in [self.action_delete, self.action_history]:
            p.setEnabled(has_any_preset and not preset.is_included_preset)

        self.action_export.setEnabled(has_valid_preset and not preset.is_included_preset)

        for p in [self.action_customize, self.action_duplicate, self.action_map_tracker, self.action_required_tricks]:
            p.setEnabled(has_valid_preset)


class SelectPresetWidget(QtWidgets.QWidget, Ui_SelectPresetWidget):
    CanGenerate = QtCore.Signal(bool)
    for_multiworld: bool = False

    _logic_settings_window: CustomizePresetDialog | None = None
    _preset_history: PresetHistoryDialog | None = None
    _has_set_from_last_selected: bool = False
    _preset_menu: PresetMenu
    _window_manager: WindowManager
    _options: Options
    _game: RandovaniaGame
    _can_generate: bool = False

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.setupUi(self)

    def setup_ui(self, game: RandovaniaGame, window_manager: WindowManager, options: Options):
        self._window_manager = window_manager
        self._options = options
        self._game = game

        self.create_preset_tree.game = game
        self.create_preset_tree.preset_manager = self._window_manager.preset_manager
        self.create_preset_tree.options = self._options

        # Menu
        self._preset_menu = PresetMenu(self)

        # Signals
        self.create_preset_tree.itemSelectionChanged.connect(self._on_select_preset)
        self.create_preset_tree.customContextMenuRequested.connect(self._on_tree_context_menu)

        self._preset_menu.action_customize.triggered.connect(self._on_customize_preset)
        self._preset_menu.action_delete.triggered.connect(self._on_delete_preset)
        self._preset_menu.action_history.triggered.connect(self._on_view_preset_history)
        self._preset_menu.action_export.triggered.connect(self._on_export_preset)
        self._preset_menu.action_duplicate.triggered.connect(self._on_duplicate_preset)
        self._preset_menu.action_map_tracker.triggered.connect(self._on_open_map_tracker_for_preset)
        self._preset_menu.action_required_tricks.triggered.connect(self._on_open_required_tricks_for_preset)
        self._preset_menu.action_import.triggered.connect(self._on_import_preset)
        self._preset_menu.action_view_deleted.triggered.connect(self._on_view_deleted)
        self.create_preset_description.linkActivated.connect(self._on_click_create_preset_description)

        self._update_preset_tree_items()
        self.on_preset_changed(None)

    def _update_preset_tree_items(self):
        self.create_preset_tree.update_items()

    @property
    def _current_preset_data(self) -> VersionedPreset | None:
        return self.create_preset_tree.current_preset_data

    def _add_new_preset(self, preset: VersionedPreset, *, parent: uuid.UUID | None):
        with self._options as options:
            options.set_parent_for_preset(preset.uuid, parent)
            options.set_selected_preset_uuid_for(self._game, preset.uuid)

        self._window_manager.preset_manager.add_new_preset(preset)
        self._update_preset_tree_items()
        self.create_preset_tree.select_preset(preset)

    @asyncSlot()
    async def _on_customize_preset(self):
        if self._logic_settings_window is not None:
            self._logic_settings_window.raise_()
            return

        monitoring.metrics.incr("gui_preset_customize_clicked")

        old_preset = self._current_preset_data.get_preset()
        if self._current_preset_data.is_included_preset:
            parent_uuid = old_preset.uuid
            old_preset = old_preset.fork()
        else:
            parent_uuid = self._options.get_parent_for_preset(old_preset.uuid)

        editor = PresetEditor(old_preset, self._options)
        self._logic_settings_window = CustomizePresetDialog(self._window_manager, editor)
        self._logic_settings_window.on_preset_changed(editor.create_custom_preset_with())
        editor.on_changed = lambda: self._logic_settings_window.on_preset_changed(editor.create_custom_preset_with())

        result = await async_dialog.execute_dialog(self._logic_settings_window)
        self._logic_settings_window.deleteLater()
        self._logic_settings_window = None

        if result == QtWidgets.QDialog.DialogCode.Accepted:
            self._add_new_preset(
                VersionedPreset.with_preset(editor.create_custom_preset_with()),
                parent=parent_uuid,
            )

    @asyncSlot()
    async def _on_delete_preset(self):
        monitoring.metrics.incr("gui_preset_delete_clicked")
        result = await async_dialog.warning(
            self,
            "Delete preset?",
            f"Are you sure you want to delete preset {self._current_preset_data.name}?",
            buttons=async_dialog.StandardButton.Yes | async_dialog.StandardButton.No,
            default_button=async_dialog.StandardButton.No,
        )
        if result == async_dialog.StandardButton.Yes:
            monitoring.metrics.incr("gui_preset_delete_confirmed")
            self._window_manager.preset_manager.delete_preset(self._current_preset_data)
            self._update_preset_tree_items()
            self._on_select_preset()

    @asyncSlot()
    async def _on_view_preset_history(self):
        monitoring.metrics.incr("gui_preset_history_clicked")
        if self._preset_history is not None:
            return await async_dialog.warning(
                self, "Dialog already open", "Another preset history dialog is already open. Please close it first."
            )

        preset = self._current_preset_data
        assert preset is not None
        self._preset_history = PresetHistoryDialog(self._window_manager.preset_manager, preset)

        result = await async_dialog.execute_dialog(self._preset_history)
        new_preset = self._preset_history.selected_preset()
        self._preset_history = None

        if result == QtWidgets.QDialog.DialogCode.Accepted:
            assert new_preset is not None
            self._window_manager.preset_manager.add_new_preset(VersionedPreset.with_preset(new_preset))
            self._update_preset_tree_items()

    def _on_export_preset(self):
        default_name = f"{self._current_preset_data.slug_name}.rdvpreset"
        path = common_qt_lib.prompt_user_for_preset_file(self._window_manager, new_file=True, name=default_name)
        if path is not None:
            try:
                self._current_preset_data.save_to_file(path)
            except OSError as e:
                QtWidgets.QMessageBox.critical(
                    self, "Unable to save", f"The following error occurred when writing to '{path}': {e}."
                )

    def _on_duplicate_preset(self):
        old_preset = self._current_preset_data
        new_preset = VersionedPreset.with_preset(old_preset.get_preset().fork())
        self._add_new_preset(new_preset, parent=old_preset.uuid)

    @asyncSlot()
    async def _on_open_map_tracker_for_preset(self):
        await self._window_manager.open_map_tracker(self._current_preset_data.get_preset())

    def _on_open_required_tricks_for_preset(self):
        from randovania.gui.dialog.trick_usage_popup import TrickUsagePopup

        self._trick_usage_popup = TrickUsagePopup(self, self._window_manager, self._current_preset_data.get_preset())
        self._trick_usage_popup.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
        self._trick_usage_popup.open()

    def _on_import_preset(self):
        monitoring.metrics.incr("gui_preset_import_clicked")
        path = common_qt_lib.prompt_user_for_preset_file(self._window_manager, new_file=False)
        if path is not None:
            self.import_preset_file(path)

    def _on_view_deleted(self):
        raise RuntimeError("Feature not implemented")

    def import_preset_file(self, path: Path):
        try:
            preset = VersionedPreset.from_file_sync(path)
            preset.get_preset()
        except (InvalidPreset, json.JSONDecodeError):
            QtWidgets.QMessageBox.critical(
                self._window_manager, "Error loading preset", f"The file at '{path}' contains an invalid preset."
            )
            return

        existing_preset = self._window_manager.preset_manager.preset_for_uuid(preset.uuid)
        if existing_preset is not None:
            user_response = QtWidgets.QMessageBox.warning(
                self._window_manager,
                "Preset ID conflict",
                f"The new preset '{preset.name}' has the same ID as existing '{existing_preset.name}'. "
                f"Do you want to overwrite it?",
                async_dialog.StandardButton.Yes | async_dialog.StandardButton.No | async_dialog.StandardButton.Cancel,
                async_dialog.StandardButton.Cancel,
            )
            if user_response == async_dialog.StandardButton.Cancel:
                return
            elif user_response == async_dialog.StandardButton.No:
                preset = VersionedPreset.with_preset(dataclasses.replace(preset.get_preset(), uuid=uuid.uuid4()))

        self._add_new_preset(preset, parent=None)

    def _on_select_preset(self):
        preset_data = self._current_preset_data
        self.on_preset_changed(preset_data)

        if preset_data is not None:
            with self._options as options:
                options.set_selected_preset_uuid_for(self._game, preset_data.uuid)

    def _on_tree_context_menu(self, pos: QtCore.QPoint):
        item: QtWidgets.QTreeWidgetItem = self.create_preset_tree.itemAt(pos)
        preset = None
        if item is not None:
            preset = self.create_preset_tree.preset_for_item(item)

        self._preset_menu.set_preset(preset)
        self._preset_menu.exec(QtGui.QCursor.pos())

    @property
    def preset(self) -> VersionedPreset | None:
        return self._current_preset_data

    def on_options_changed(self, options: Options):
        if not self._has_set_from_last_selected:
            self._has_set_from_last_selected = True
            preset_manager = self._window_manager.preset_manager
            preset = preset_manager.preset_for_uuid(options.selected_preset_uuid_for(self._game))
            if preset is None:
                preset = preset_manager.default_preset_for_game(self._game)
            self.create_preset_tree.select_preset(preset)

    def on_preset_changed(self, preset: VersionedPreset | None):
        can_generate = False
        if preset is None:
            description = "Please select a preset from the list."

        else:
            try:
                raw_preset = preset.get_preset()

                incompatible = self.for_multiworld and raw_preset.settings_incompatible_with_multiworld()
                if incompatible:
                    description = "The following settings are incompatible with multiworld:\n" + "\n".join(incompatible)
                else:
                    can_generate = True
                    formatted_description = markdown.markdown(raw_preset.description)
                    description = f"<p style='font-weight:600;'>{raw_preset.name}</p><p>{formatted_description}</p>"
                    description += preset_describer.merge_categories(preset_describer.describe(raw_preset))

            except InvalidPreset as e:
                if isinstance(e.original_exception, UnsupportedVersion):
                    exception_desc = f"<p>{e.original_exception}</p>"
                else:
                    logging.warning(f"Invalid preset for {preset.name}")
                    exception_desc = "<pre>{}</pre>".format("\n".join(traceback.format_exception(e.original_exception)))

                description = (
                    f"<p>Preset {preset.name} can't be used as it contains errors.</p>"
                    f"<p>Please edit the file named <a href='open-preset://{preset.uuid}'>{preset.uuid}</a> manually "
                    f"or delete this preset.</p>"
                    f"{exception_desc}"
                )

        self.create_preset_description.setText(description)
        self._can_generate = can_generate
        self.CanGenerate.emit(can_generate)

    def _on_click_create_preset_description(self, link: str):
        info = re.match(r"^open-preset://([0-9a-f\-]{36})$", link)
        if info is None:
            return

        path = self._window_manager.preset_manager.data_dir
        if path is None:
            return

        common_qt_lib.open_directory_in_explorer(
            path,
            common_qt_lib.FallbackDialog(
                "Preset",
                f"The selected preset can be found at:\n{path}",
                self,
            ),
        )

    def change_game(self, game: RandovaniaGame):
        self._game = game
        self.create_preset_tree.game = game
        self.create_preset_tree.update_items()
        self.on_preset_changed(None)
