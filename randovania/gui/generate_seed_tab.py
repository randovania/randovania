import dataclasses
import datetime
import logging
import random
import uuid
from functools import partial
from pathlib import Path
from typing import Optional, Callable

from PySide2 import QtWidgets, QtCore, QtGui
from PySide2.QtCore import QTimer
from qasync import asyncSlot

from randovania.gui.generated.main_window_ui import Ui_MainWindow
from randovania.gui.lib import preset_describer, common_qt_lib, async_dialog
from randovania.gui.lib.background_task_mixin import BackgroundTaskMixin
from randovania.gui.lib.generation_failure_handling import GenerationFailureHandler
from randovania.gui.lib.window_manager import WindowManager
from randovania.gui.preset_settings.logic_settings_window import LogicSettingsWindow
from randovania.interface_common import simplified_patcher
from randovania.interface_common.options import Options
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.layout_description import LayoutDescription
from randovania.layout.permalink import Permalink
from randovania.layout.preset_migration import VersionedPreset, InvalidPreset
from randovania.lib.status_update_lib import ProgressUpdateCallable
from randovania.resolver.exceptions import GenerationFailure


def persist_layout(history_dir: Path, description: LayoutDescription):
    history_dir.mkdir(parents=True, exist_ok=True)

    games = "-".join(sorted(game.short_name for game in description.all_games))

    date_format = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    file_path = history_dir.joinpath(
        f"{date_format}_{games}_{description.shareable_word_hash}.{description.file_extension()}")
    description.save_to_file(file_path)


class PresetMenu(QtWidgets.QMenu):
    action_customize: QtWidgets.QAction
    action_delete: QtWidgets.QAction
    action_history: QtWidgets.QAction
    action_export: QtWidgets.QAction
    action_duplicate: QtWidgets.QAction
    action_map_tracker: QtWidgets.QAction
    action_required_tricks: QtWidgets.QAction

    action_import: QtWidgets.QAction
    action_view_deleted: QtWidgets.QAction

    preset: Optional[VersionedPreset]

    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)
        self.action_customize = QtWidgets.QAction(parent)
        self.action_delete = QtWidgets.QAction(parent)
        self.action_history = QtWidgets.QAction(parent)
        self.action_export = QtWidgets.QAction(parent)
        self.action_duplicate = QtWidgets.QAction(parent)
        self.action_map_tracker = QtWidgets.QAction(parent)
        self.action_required_tricks = QtWidgets.QAction(parent)
        self.action_import = QtWidgets.QAction(parent)
        self.action_view_deleted = QtWidgets.QAction(parent)

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
        self.action_history.setVisible(False)
        self.action_view_deleted.setVisible(False)

    def set_preset(self, preset: Optional[VersionedPreset]):
        self.preset = preset

        for p in [self.action_delete, self.action_history, self.action_export]:
            p.setEnabled(preset is not None and preset.base_preset_uuid is not None)

        for p in [self.action_customize, self.action_duplicate, self.action_map_tracker, self.action_required_tricks]:
            p.setEnabled(preset is not None)


class GenerateSeedTab(QtWidgets.QWidget, BackgroundTaskMixin):
    _logic_settings_window: Optional[LogicSettingsWindow] = None
    _has_set_from_last_selected: bool = False
    _preset_menu: PresetMenu
    _action_delete: QtWidgets.QAction
    _original_show_event: Callable[[QtGui.QShowEvent], None]

    def __init__(self, window: Ui_MainWindow, window_manager: WindowManager, options: Options):
        super().__init__()

        self.window = window
        self._window_manager = window_manager
        self.failure_handler = GenerationFailureHandler(self)
        self._options = options

    def setup_ui(self):
        window = self.window
        window.create_preset_tree.window_manager = self._window_manager

        self._original_show_event = window.tab_create_seed.showEvent
        window.tab_create_seed.showEvent = self._tab_show_event

        # Progress
        self.background_tasks_button_lock_signal.connect(self.enable_buttons_with_background_tasks)
        self.progress_update_signal.connect(self.update_progress)
        self.window.stop_background_process_button.clicked.connect(self.stop_background_process)

        self.window.num_players_spin_box.setVisible(self._window_manager.is_preview_mode)
        self.window.create_generate_no_retry_button.setVisible(self._window_manager.is_preview_mode)

        # Menu
        self._preset_menu = PresetMenu(window)

        # Signals
        window.create_generate_button.clicked.connect(partial(self._generate_new_seed, True))
        window.create_generate_no_retry_button.clicked.connect(partial(self._generate_new_seed, True, retries=0))
        window.create_generate_race_button.clicked.connect(partial(self._generate_new_seed, False))
        window.create_preset_tree.itemSelectionChanged.connect(self._on_select_preset)
        window.create_preset_tree.customContextMenuRequested.connect(self._on_tree_context_menu)

        self._preset_menu.action_customize.triggered.connect(self._on_customize_preset)
        self._preset_menu.action_delete.triggered.connect(self._on_delete_preset)
        self._preset_menu.action_history.triggered.connect(self._on_view_preset_history)
        self._preset_menu.action_export.triggered.connect(self._on_export_preset)
        self._preset_menu.action_duplicate.triggered.connect(self._on_duplicate_preset)
        self._preset_menu.action_map_tracker.triggered.connect(self._on_open_map_tracker_for_preset)
        self._preset_menu.action_required_tricks.triggered.connect(self._on_open_required_tricks_for_preset)
        self._preset_menu.action_import.triggered.connect(self._on_import_preset)

        self._update_preset_tree_items()

    def _update_preset_tree_items(self):
        self.window.create_preset_tree.update_items()

    @asyncSlot()
    async def _do_migration(self):
        dialog = QtWidgets.QProgressDialog(
            ("Randovania changed where your presets are saved and a one-time migration is being performed.\n"
             "Further changes in old versions won't be migrated."),
            None,
            0, 1, self,
        )
        common_qt_lib.set_default_window_icon(dialog)
        dialog.setWindowTitle("Preset Migration")
        dialog.setAutoReset(False)
        dialog.setAutoClose(False)
        dialog.show()

        def on_update(current, target):
            dialog.setValue(current)
            dialog.setMaximum(target)

        await self._window_manager.preset_manager.migrate_from_old_path(on_update)
        self._update_preset_tree_items()
        dialog.setCancelButtonText("Ok")

    def _tab_show_event(self, event: QtGui.QShowEvent):
        if self._window_manager.preset_manager.should_do_migration():
            QTimer.singleShot(0, self._do_migration)

        return self._original_show_event(event)

    @property
    def _current_preset_data(self) -> Optional[VersionedPreset]:
        return self.window.create_preset_tree.current_preset_data

    def enable_buttons_with_background_tasks(self, value: bool):
        self.window.stop_background_process_button.setEnabled(not value)
        self.window.create_generate_button.setEnabled(value)
        self.window.create_generate_race_button.setEnabled(value)

    def _add_new_preset(self, preset: VersionedPreset):
        with self._options as options:
            options.selected_preset_uuid = preset.uuid

        self._window_manager.preset_manager.add_new_preset(preset)
        self._update_preset_tree_items()
        self.window.create_preset_tree.select_preset(preset)

    @asyncSlot()
    async def _on_customize_preset(self):
        if self._logic_settings_window is not None:
            self._logic_settings_window.raise_()
            return

        old_preset = self._current_preset_data.get_preset()
        if old_preset.base_preset_uuid is None:
            old_preset = old_preset.fork()
        editor = PresetEditor(old_preset)
        self._logic_settings_window = LogicSettingsWindow(self._window_manager, editor)

        self._logic_settings_window.on_preset_changed(editor.create_custom_preset_with())
        editor.on_changed = lambda: self._logic_settings_window.on_preset_changed(editor.create_custom_preset_with())

        result = await async_dialog.execute_dialog(self._logic_settings_window)
        self._logic_settings_window = None

        if result == QtWidgets.QDialog.Accepted:
            self._add_new_preset(VersionedPreset.with_preset(editor.create_custom_preset_with()))

    def _on_delete_preset(self):
        self._window_manager.preset_manager.delete_preset(self._current_preset_data)
        self._update_preset_tree_items()
        self._on_select_preset()

    def _on_view_preset_history(self):
        pass

    def _on_export_preset(self):
        path = common_qt_lib.prompt_user_for_preset_file(self._window_manager, new_file=True)
        if path is not None:
            self._current_preset_data.save_to_file(path)

    def _on_duplicate_preset(self):
        old_preset = self._current_preset_data
        self._add_new_preset(VersionedPreset.with_preset(old_preset.get_preset().fork()))

    def _on_open_map_tracker_for_preset(self):
        self._window_manager.open_map_tracker(self._current_preset_data.get_preset())

    def _on_open_required_tricks_for_preset(self):
        from randovania.gui.dialog.trick_usage_popup import TrickUsagePopup
        self._trick_usage_popup = TrickUsagePopup(self, self._window_manager, self._current_preset_data.get_preset())
        self._trick_usage_popup.setWindowModality(QtCore.Qt.WindowModal)
        self._trick_usage_popup.open()

    def _on_import_preset(self):
        path = common_qt_lib.prompt_user_for_preset_file(self._window_manager, new_file=False)
        if path is not None:
            self.import_preset_file(path)

    def import_preset_file(self, path: Path):
        preset = VersionedPreset.from_file_sync(path)
        try:
            preset.get_preset()
        except InvalidPreset:
            QtWidgets.QMessageBox.critical(
                self._window_manager,
                "Error loading preset",
                "The file at '{}' contains an invalid preset.".format(path)
            )
            return

        existing_preset = self._window_manager.preset_manager.preset_for_uuid(preset.uuid)
        if existing_preset is not None:
            user_response = QtWidgets.QMessageBox.warning(
                self._window_manager,
                "Preset ID conflict",
                "The new preset '{}' has the same ID as existing '{}'. Do you want to overwrite it?".format(
                    preset.name,
                    existing_preset.name,
                ),
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel,
                QtWidgets.QMessageBox.Cancel
            )
            if user_response == QtWidgets.QMessageBox.Cancel:
                return
            elif user_response == QtWidgets.QMessageBox.No:
                preset = VersionedPreset.with_preset(dataclasses.replace(preset.get_preset(), uuid=uuid.uuid4()))

        self._add_new_preset(preset)

    def _on_select_preset(self):
        preset_data = self._current_preset_data
        self.on_preset_changed(preset_data)

        if preset_data is not None:
            with self._options as options:
                options.selected_preset_uuid = preset_data.uuid

    def _on_tree_context_menu(self, pos: QtCore.QPoint):
        item: QtWidgets.QTreeWidgetItem = self.window.create_preset_tree.itemAt(pos)
        preset = None
        if item is not None:
            preset = self.window.create_preset_tree.preset_for_item(item)

        self._preset_menu.set_preset(preset)
        self._preset_menu.exec_(QtGui.QCursor.pos())

    # Generate seed

    def _generate_new_seed(self, spoiler: bool, retries: Optional[int] = None):
        preset = self._current_preset_data
        num_players = self.window.num_players_spin_box.value()

        self.generate_seed_from_permalink(Permalink(
            seed_number=random.randint(0, 2 ** 31),
            spoiler=spoiler,
            presets={
                i: preset.get_preset()
                for i in range(num_players)
            },
        ), retries=retries)

    def generate_seed_from_permalink(self, permalink: Permalink, retries: Optional[int] = None):
        def work(progress_update: ProgressUpdateCallable):
            try:
                layout = simplified_patcher.generate_layout(progress_update=progress_update,
                                                            permalink=permalink,
                                                            options=self._options,
                                                            retries=retries)
                progress_update(f"Success! (Seed hash: {layout.shareable_hash})", 1)
                persist_layout(self._options.game_history_path, layout)
                self._window_manager.open_game_details(layout)

            except GenerationFailure as generate_exception:
                self.failure_handler.handle_failure(generate_exception)
                progress_update("Generation Failure: {}".format(generate_exception), -1)

        if self._window_manager.is_preview_mode:
            logging.info(f"Permalink: {permalink.as_base64_str}")
        self.run_in_background_thread(work, "Creating a seed...")

    def on_options_changed(self, options: Options):
        self.window.create_preset_tree.set_show_experimental(options.experimental_games)

        if not self._has_set_from_last_selected:
            self._has_set_from_last_selected = True
            preset = self._window_manager.preset_manager.preset_for_uuid(options.selected_preset_uuid)
            if preset is None:
                preset = self._window_manager.preset_manager.default_preset
            self.window.create_preset_tree.select_preset(preset)

    def on_preset_changed(self, preset: Optional[VersionedPreset]):
        can_generate = False
        if preset is None:
            description = "Please select a preset from the list, not a game."

        else:
            try:
                raw_preset = preset.get_preset()
                can_generate = True
                description = f"<p style='font-weight:600;'>{raw_preset.name}</p><p>{raw_preset.description}</p>"
                description += preset_describer.merge_categories(preset_describer.describe(raw_preset))

            except InvalidPreset as e:
                logging.exception(f"Invalid preset for {preset.name}")
                description = (
                    f"Preset {preset.name} can't be used as it contains the following error:"
                    f"\n{e.original_exception}\n"
                    f"\nPlease open edit the preset file with id {preset.uuid} manually or delete this preset."
                )

        self.window.create_preset_description.setText(description)
        for btn in [self.window.create_generate_button, self.window.create_generate_race_button]:
            btn.setEnabled(can_generate)

    def update_progress(self, message: str, percentage: int):
        self.window.progress_label.setText(message)
        if "Aborted" in message:
            percentage = 0
        if percentage >= 0:
            self.window.progress_bar.setRange(0, 100)
            self.window.progress_bar.setValue(percentage)
        else:
            self.window.progress_bar.setRange(0, 0)
