import asyncio
import json
import os
from pathlib import Path
from typing import Optional

import markdown
from PySide2 import QtCore, QtWidgets
from PySide2.QtCore import QUrl, Signal
from PySide2.QtGui import QDesktopServices
from PySide2.QtWidgets import QMainWindow, QAction, QMessageBox

from randovania import VERSION
from randovania.game_description import default_database
from randovania.game_description.node import LogbookNode, LoreType
from randovania.games.prime import default_data
from randovania.gui.background_task_mixin import BackgroundTaskMixin
from randovania.gui.common_qt_lib import prompt_user_for_seed_log, prompt_user_for_database_file, \
    set_default_window_icon
from randovania.gui.data_editor import DataEditorWindow
from randovania.gui.mainwindow_ui import Ui_MainWindow
from randovania.gui.seed_details_window import SeedDetailsWindow
from randovania.gui.tab_service import TabService
from randovania.gui.tracker_window import TrackerWindow, InvalidLayoutForTracker
from randovania.interface_common import github_releases_data, update_checker
from randovania.interface_common.options import Options
from randovania.resolver import debug


_DISABLE_VALIDATION_WARNING = """
<html><head/><body>
<p>While it sometimes throws errors, the validation is what guarantees that your seed is completable.<br/>
Do <span style=" font-weight:600;">not</span> disable if you're uncomfortable with possibly unbeatable seeds.
</p><p align="center">Are you sure you want to disable validation?</p></body></html>
"""


class MainWindow(QMainWindow, Ui_MainWindow, TabService, BackgroundTaskMixin):
    newer_version_signal = Signal(str, str)
    options_changed_signal = Signal()
    is_preview_mode: bool = False

    menu_new_version: Optional[QAction] = None
    _current_version_url: Optional[str] = None
    _options: Options
    _data_visualizer: Optional[DataEditorWindow] = None

    @property
    def _tab_widget(self):
        return self.tabWidget

    def __init__(self, options: Options, preview: bool):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("Randovania {}".format(VERSION))
        self.is_preview_mode = preview
        self.setAcceptDrops(True)
        set_default_window_icon(self)

        self.intro_label.setText(self.intro_label.text().format(version=VERSION))

        if preview:
            debug._DEBUG_LEVEL = 2

        # Signals
        self.newer_version_signal.connect(self.display_new_version)
        self.background_tasks_button_lock_signal.connect(self.enable_buttons_with_background_tasks)
        self.progress_update_signal.connect(self.update_progress)
        self.stop_background_process_button.clicked.connect(self.stop_background_process)
        self.options_changed_signal.connect(self.on_options_changed)

        # Menu Bar
        self.menu_action_data_visualizer.triggered.connect(self._open_data_visualizer)
        self.menu_action_existing_seed_details.triggered.connect(self._open_existing_seed_details)
        self.menu_action_tracker.triggered.connect(self._open_tracker)
        self.menu_action_edit_new_database.triggered.connect(self._open_data_editor_default)
        self.menu_action_edit_existing_database.triggered.connect(self._open_data_editor_prompt)
        self.menu_action_export_iso.triggered.connect(self._export_iso)
        self.menu_action_validate_seed_after.triggered.connect(self._on_validate_seed_change)
        self.menu_action_timeout_generation_after_a_time_limit.triggered.connect(self._on_generate_time_limit_change)

        self.menu_action_export_iso.setEnabled(False)

        _translate = QtCore.QCoreApplication.translate
        self.tabs = []

        from randovania.gui.game_patches_window import GamePatchesWindow
        from randovania.gui.iso_management_window import ISOManagementWindow
        from randovania.gui.logic_settings_window import LogicSettingsWindow
        from randovania.gui.cosmetic_window import CosmeticWindow
        from randovania.gui.main_rules import MainRulesWindow

        self.tab_windows = [
            (ISOManagementWindow, "ROM Settings"),
            (GamePatchesWindow, "Game Patches"),
            (MainRulesWindow, "Main Rules"),
            (LogicSettingsWindow, "Logic Settings"),
            (CosmeticWindow, "Cosmetic"),
        ]

        for i, tab in enumerate(self.tab_windows):
            self.windows.append(tab[0](self, self, options))
            self.tabs.append(self.windows[i].centralWidget)
            self.tabWidget.insertTab(i + 1, self.tabs[i], _translate("MainWindow", tab[1]))

        # Setting this event only now, so all options changed trigger only once
        options.on_options_changed = self.options_changed_signal.emit
        self._options = options
        with options:
            self.on_options_changed()

        self.tabWidget.setCurrentIndex(0)

        # Update hints text
        self._update_hints_text()

    def closeEvent(self, event):
        self.stop_background_process()
        for window in self.windows:
            window.closeEvent(event)
        super().closeEvent(event)

    def dragEnterEvent(self, event):
        for url in event.mimeData().urls():
            if os.path.splitext(url.toLocalFile())[1] == ".iso":
                event.acceptProposedAction()
                return

    def dropEvent(self, event):
        from randovania.gui.iso_management_window import ISOManagementWindow

        for url in event.mimeData().urls():
            iso_path = url.toLocalFile()
            if os.path.splitext(iso_path)[1] == ".iso":
                self.get_tab(ISOManagementWindow).load_game(Path(iso_path))
                return

    # Releases info
    def request_new_data(self):
        asyncio.get_event_loop().create_task(github_releases_data.get_releases()).add_done_callback(
            self._on_releases_data)

    def _on_releases_data(self, task: asyncio.Task):
        releases = task.result()
        current_version = update_checker.strict_current_version()
        last_changelog = self._options.last_changelog_displayed

        all_change_logs, new_change_logs, version_to_display = update_checker.versions_to_display_for_releases(
            current_version, last_changelog, releases)

        if version_to_display is not None:
            self.display_new_version(version_to_display)

        if all_change_logs:
            changelog_tab = QtWidgets.QWidget()
            changelog_tab.setObjectName("changelog_tab")
            changelog_tab_layout = QtWidgets.QVBoxLayout(changelog_tab)
            changelog_tab_layout.setObjectName("changelog_tab_layout")
            changelog_scroll_area = QtWidgets.QScrollArea(changelog_tab)
            changelog_scroll_area.setWidgetResizable(True)
            changelog_scroll_area.setObjectName("changelog_scroll_area")
            changelog_scroll_contents = QtWidgets.QWidget()
            changelog_scroll_contents.setGeometry(QtCore.QRect(0, 0, 489, 337))
            changelog_scroll_contents.setObjectName("changelog_scroll_contents")
            changelog_scroll_layout = QtWidgets.QVBoxLayout(changelog_scroll_contents)
            changelog_scroll_layout.setObjectName("changelog_scroll_layout")
            changelog_label = QtWidgets.QLabel(changelog_scroll_contents)
            changelog_label.setObjectName("changelog_label")
            changelog_label.setText(markdown.markdown("\n".join(all_change_logs)))
            changelog_scroll_layout.addWidget(changelog_label)
            changelog_scroll_area.setWidget(changelog_scroll_contents)
            changelog_tab_layout.addWidget(changelog_scroll_area)
            self.welcome_tab_widget.addTab(changelog_tab, "Change Log")

        if new_change_logs:
            QMessageBox.information(self, "What's new", markdown.markdown("\n".join(new_change_logs)))
            with self._options as options:
                options.last_changelog_displayed = current_version

    def display_new_version(self, version: update_checker.VersionDescription):
        if self.menu_new_version is None:
            self.menu_new_version = QAction("", self)
            self.menu_new_version.triggered.connect(self.open_version_link)
            self.menu_bar.addAction(self.menu_new_version)

        self.menu_new_version.setText("New version available: {}".format(version.tag_name))
        self._current_version_url = version.html_url

    def open_version_link(self):
        if self._current_version_url is None:
            raise RuntimeError("Called open_version_link, but _current_version_url is None")

        QDesktopServices.openUrl(QUrl(self._current_version_url))

    # Options
    def on_options_changed(self):
        for window in self.windows:
            window.on_options_changed(self._options)

        self.menu_action_validate_seed_after.setChecked(self._options.advanced_validate_seed_after)
        self.menu_action_timeout_generation_after_a_time_limit.setChecked(
            self._options.advanced_timeout_during_generation)

    # Menu Actions
    def _open_data_visualizer(self):
        self.open_data_visualizer_at(None, None)

    def open_data_visualizer_at(self,
                                world_name: Optional[str],
                                area_name: Optional[str],
                                ):
        self._data_visualizer = DataEditorWindow(default_data.decode_default_prime2(), False)

        if world_name is not None:
            self._data_visualizer.focus_on_world(world_name)

        if area_name is not None:
            self._data_visualizer.focus_on_area(area_name)

        self._data_visualizer.show()

    def _open_data_editor_default(self):
        self._data_editor = DataEditorWindow(default_data.decode_default_prime2(), True)
        self._data_editor.show()

    def _open_data_editor_prompt(self):
        database_path = prompt_user_for_database_file(self)
        if database_path is None:
            return

        with database_path.open("r") as database_file:
            self._data_editor = DataEditorWindow(json.load(database_file), True)
            self._data_editor.show()

    def _open_existing_seed_details(self):
        json_path = prompt_user_for_seed_log(self)
        if json_path is None:
            return

        self._seed_details = SeedDetailsWindow(json_path)
        self._seed_details.show()

    def _open_tracker(self):
        try:
            self._tracker = TrackerWindow(self._options.tracker_files_path, self._options.layout_configuration)
        except InvalidLayoutForTracker as e:
            QMessageBox.critical(
                self,
                "Unsupported configuration for Tracker",
                str(e)
            )
            return

        self._tracker.show()

    def _export_iso(self):
        pass

    def _on_validate_seed_change(self):
        old_value = self._options.advanced_validate_seed_after
        new_value = self.menu_action_validate_seed_after.isChecked()

        if old_value and not new_value:
            box = QMessageBox(self)
            box.setWindowTitle("Disable validation?")
            box.setText(_DISABLE_VALIDATION_WARNING)
            box.setIcon(QMessageBox.Warning)
            box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            box.setDefaultButton(QMessageBox.No)
            user_response = box.exec_()
            if user_response != QMessageBox.Yes:
                self.menu_action_validate_seed_after.setChecked(True)
                return

        with self._options as options:
            options.advanced_validate_seed_after = new_value

    def _on_generate_time_limit_change(self):
        is_checked = self.menu_action_timeout_generation_after_a_time_limit.isChecked()
        with self._options as options:
            options.advanced_timeout_during_generation = is_checked

    def _update_hints_text(self):
        game_description = default_database.default_prime2_game_description()

        number_for_hint_type = {
            hint_type: i + 1
            for i, hint_type in enumerate(LoreType)
        }
        used_hint_types = set()

        self.hint_tree_widget.setSortingEnabled(False)

        for world in game_description.world_list.worlds:

            world_item = QtWidgets.QTreeWidgetItem(self.hint_tree_widget)
            world_item.setText(0, world.name)
            world_item.setExpanded(True)

            for area in world.areas:
                hint_types = {}

                for node in area.nodes:
                    if isinstance(node, LogbookNode):
                        if node.required_translator is not None:
                            hint_types[node.lore_type] = node.required_translator.short_name
                        else:
                            hint_types[node.lore_type] = "✓"

                if hint_types:
                    area_item = QtWidgets.QTreeWidgetItem(world_item)
                    area_item.setText(0, area.name)

                    for hint_type, text in hint_types.items():
                        area_item.setText(number_for_hint_type[hint_type], text)
                        used_hint_types.add(hint_type)

        self.hint_tree_widget.resizeColumnToContents(0)
        self.hint_tree_widget.setSortingEnabled(True)
        self.hint_tree_widget.sortByColumn(0, QtCore.Qt.AscendingOrder)

        for hint_type in used_hint_types:
            self.hint_tree_widget.headerItem().setText(number_for_hint_type[hint_type], hint_type.long_name)

    # Background Process

    def enable_buttons_with_background_tasks(self, value: bool):
        self.stop_background_process_button.setEnabled(not value)

    def update_progress(self, message: str, percentage: int):
        self.progress_label.setText(message)
        if "Aborted" in message:
            percentage = 0
        if percentage >= 0:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(percentage)
        else:
            self.progress_bar.setRange(0, 0)
