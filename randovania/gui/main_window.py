from __future__ import annotations

import base64
import functools
import json
import logging
import os
import typing
from functools import partial
from pathlib import Path
from typing import Optional, List

from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtCore import QUrl, Signal, Qt
from qasync import asyncSlot

import randovania
from randovania import VERSION, get_readme
from randovania.game_description.resources.trick_resource_info import TrickResourceInfo
from randovania.games.game import RandovaniaGame
from randovania.gui.generated.main_window_ui import Ui_MainWindow
from randovania.gui.lib import common_qt_lib, async_dialog, theme
from randovania.gui.lib.common_qt_lib import open_directory_in_explorer
from randovania.gui.lib.trick_lib import used_tricks, difficulties_for_trick
from randovania.gui.lib.window_manager import WindowManager
from randovania.interface_common import update_checker
from randovania.interface_common.options import Options
from randovania.interface_common.preset_manager import PresetManager
from randovania.layout.base.trick_level import LayoutTrickLevel
from randovania.layout.layout_description import LayoutDescription
from randovania.lib import enum_lib
from randovania.resolver import debug

if typing.TYPE_CHECKING:
    from randovania.layout.permalink import Permalink

_DISABLE_VALIDATION_WARNING = """
<html><head/><body>
<p>While it sometimes throws errors, the validation is what guarantees that your seed is completable.<br/>
Do <span style=" font-weight:600;">not</span> disable if you're uncomfortable with possibly unbeatable seeds.
</p><p align="center">Are you sure you want to disable validation?</p></body></html>
"""


def _t(key: str, disambiguation: Optional[str] = None):
    return QtCore.QCoreApplication.translate("MainWindow", key, disambiguation)


def _update_label_on_show(label: QtWidgets.QLabel, text: str):
    def showEvent(_):
        if label._delayed_text is not None:
            label.setText(label._delayed_text)
            label._delayed_text = None

    label._delayed_text = text
    label.showEvent = showEvent


class MainWindow(WindowManager, Ui_MainWindow):
    options_changed_signal = Signal()
    _is_preview_mode: bool = False
    _experimental_games_visible: bool = False

    menu_new_version: Optional[QtGui.QAction] = None
    _current_version_url: Optional[str] = None
    _options: Options
    _data_visualizer: Optional[QtWidgets.QWidget] = None
    _map_tracker: QtWidgets.QWidget
    _preset_manager: PresetManager
    generate_seed_tab = None
    GameDetailsSignal = Signal(LayoutDescription)

    InitPostShowSignal = Signal()

    @property
    def _tab_widget(self):
        return self.main_tab_widget

    @property
    def preset_manager(self) -> PresetManager:
        return self._preset_manager

    @property
    def main_window(self) -> QtWidgets.QMainWindow:
        return self

    @property
    def is_preview_mode(self) -> bool:
        return self._is_preview_mode

    def __init__(self, options: Options, preset_manager: PresetManager,
                 network_client, preview: bool):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("Randovania {}".format(VERSION))
        self._is_preview_mode = preview
        self.setAcceptDrops(True)
        common_qt_lib.set_default_window_icon(self)

        self.setup_about_text()
        self.setup_welcome_text()
        self.browse_racetime_label.setText(self.browse_racetime_label.text().replace("color:#0000ff;", ""))

        self._preset_manager = preset_manager
        self.network_client = network_client

        if preview:
            debug.set_level(2)

        if randovania.is_frozen():
            self.menu_bar.removeAction(self.menu_edit.menuAction())

        # Signals
        self.options_changed_signal.connect(self.on_options_changed)
        self.GameDetailsSignal.connect(self._open_game_details)
        self.InitPostShowSignal.connect(self.initialize_post_show)

        self.intro_play_now_button.clicked.connect(lambda: self.main_tab_widget.setCurrentWidget(self.tab_play))
        self.open_faq_button.clicked.connect(self._open_faq)
        self.open_database_viewer_button.clicked.connect(partial(self._open_data_visualizer_for_game,
                                                                 RandovaniaGame.METROID_PRIME_ECHOES))

        self.import_permalink_button.clicked.connect(self._import_permalink)
        self.import_game_file_button.clicked.connect(self._import_spoiler_log)
        self.browse_racetime_button.clicked.connect(self._browse_racetime)
        self.create_new_seed_button.clicked.connect(
            lambda: self.main_tab_widget.setCurrentWidget(self.tab_create_seed))

        # Menu Bar
        self.game_menus = []
        self.menu_action_edits = []

        for game in RandovaniaGame.sorted_all_games():
            # Sub-Menu in Open Menu
            game_menu = QtWidgets.QMenu(self.menu_open)
            game_menu.setTitle(_t(game.long_name))
            game_menu.game = game

            if game.data.development_state.can_view(False):
                self.menu_open.addAction(game_menu.menuAction())
            self.game_menus.append(game_menu)

            game_trick_details_menu = QtWidgets.QMenu(game_menu)
            game_trick_details_menu.setTitle(_t("Trick Details"))
            self._setup_trick_difficulties_menu_on_show(game_trick_details_menu, game)

            game_data_visualizer_action = QtGui.QAction(game_menu)
            game_data_visualizer_action.setText(_t("Data Visualizer"))
            game_data_visualizer_action.triggered.connect(partial(self._open_data_visualizer_for_game, game))

            game_menu.addAction(game_trick_details_menu.menuAction())
            game_menu.addAction(game_data_visualizer_action)

            # Data Editor
            action = QtGui.QAction(self)
            action.setText(_t(game.long_name))
            self.menu_internal.addAction(action)
            action.triggered.connect(partial(self._open_data_editor_for_game, game))
            self.menu_action_edits.append(action)

        self.menu_action_edit_existing_database.triggered.connect(self._open_data_editor_prompt)
        self.menu_action_validate_seed_after.triggered.connect(self._on_validate_seed_change)
        self.menu_action_timeout_generation_after_a_time_limit.triggered.connect(self._on_generate_time_limit_change)
        self.menu_action_dark_mode.triggered.connect(self._on_menu_action_dark_mode)
        self.menu_action_experimental_games.triggered.connect(self._on_menu_action_experimental_games)
        self.menu_action_open_auto_tracker.triggered.connect(self._open_auto_tracker)
        self.menu_action_previously_generated_games.triggered.connect(self._on_menu_action_previously_generated_games)
        self.menu_action_log_files_directory.triggered.connect(self._on_menu_action_log_files_directory)
        self.menu_action_layout_editor.triggered.connect(self._on_menu_action_layout_editor)

        # Setting this event only now, so all options changed trigger only once
        options.on_options_changed = self.options_changed_signal.emit
        self._options = options

        self.main_tab_widget.setCurrentIndex(0)

    def closeEvent(self, event):
        if self.generate_seed_tab is not None:
            self.generate_seed_tab.stop_background_process()
        super().closeEvent(event)

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent):
        from randovania.layout.versioned_preset import VersionedPreset

        valid_extensions = [
            LayoutDescription.file_extension(),
            VersionedPreset.file_extension(),
        ]
        valid_extensions_with_dot = {
            f".{extension}"
            for extension in valid_extensions
        }

        for url in event.mimeData().urls():
            ext = os.path.splitext(url.toLocalFile())[1]
            if ext in valid_extensions_with_dot:
                event.acceptProposedAction()
                return

    def dropEvent(self, event: QtGui.QDropEvent):
        from randovania.layout.versioned_preset import VersionedPreset

        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.suffix == f".{LayoutDescription.file_extension()}":
                self.open_game_details(LayoutDescription.from_file(path))
                return

            elif path.suffix == f".{VersionedPreset.file_extension()}":
                self.main_tab_widget.setCurrentWidget(self.tab_create_seed)
                self.generate_seed_tab.import_preset_file(path)
                return

    def showEvent(self, event: QtGui.QShowEvent):
        self.InitPostShowSignal.emit()

    # Per-Game elements
    def refresh_game_list(self):
        self.games_tab.set_experimental_visible(self.menu_action_experimental_games.isChecked())

        if self._experimental_games_visible == self.menu_action_experimental_games.isChecked():
            return
        self._experimental_games_visible = self.menu_action_experimental_games.isChecked()

        for game_menu in self.game_menus:
            self.menu_open.removeAction(game_menu.menuAction())

        for game_menu, edit_action in zip(self.game_menus, self.menu_action_edits):
            game: RandovaniaGame = game_menu.game
            if game.data.development_state.can_view(self.menu_action_experimental_games.isChecked()):
                self.menu_open.addAction(game_menu.menuAction())

    # Delayed Initialization
    @asyncSlot()
    async def initialize_post_show(self):
        self.InitPostShowSignal.disconnect(self.initialize_post_show)
        logging.info("Will initialize things in post show")
        await self._initialize_post_show_body()
        logging.info("Finished initializing post show")

    async def _initialize_post_show_body(self):
        logging.info("Will load OnlineInteractions")
        from randovania.gui.main_online_interaction import OnlineInteractions
        logging.info("Creating OnlineInteractions...")
        self.online_interactions = OnlineInteractions(self, self.preset_manager, self.network_client, self,
                                                      self._options)

        logging.info("Will load GenerateSeedTab")
        from randovania.gui.generate_seed_tab import GenerateSeedTab
        logging.info("Creating GenerateSeedTab...")
        self.generate_seed_tab = GenerateSeedTab(self, self, self._options)
        logging.info("Running GenerateSeedTab.setup_ui")
        self.generate_seed_tab.setup_ui()

        logging.info("Will update for modified options")
        with self._options:
            self.on_options_changed()

    # Generate Seed
    def _open_faq(self):
        self.main_tab_widget.setCurrentWidget(self.games_tab)

    async def generate_seed_from_permalink(self, permalink: Permalink):
        from randovania.lib.status_update_lib import ProgressUpdateCallable
        from randovania.gui.dialog.background_process_dialog import BackgroundProcessDialog

        def work(progress_update: ProgressUpdateCallable):
            from randovania.interface_common import simplified_patcher
            layout = simplified_patcher.generate_layout(progress_update=progress_update,
                                                        parameters=permalink.parameters,
                                                        options=self._options)
            progress_update(f"Success! (Seed hash: {layout.shareable_hash})", 1)
            return layout

        new_layout = await BackgroundProcessDialog.open_for_background_task(work, "Creating a game...")

        if permalink.seed_hash is not None and permalink.seed_hash != new_layout.shareable_hash_bytes:
            response = await async_dialog.warning(
                self, "Unexpected hash",
                "Expected has to be {}. got {}. Do you wish to continue?".format(
                    base64.b32encode(permalink.seed_hash).decode(),
                    new_layout.shareable_hash,
                ),
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            )
            if response != QtWidgets.QMessageBox.Yes:
                return

        self.open_game_details(new_layout)

    @asyncSlot()
    async def _import_permalink(self):
        from randovania.gui.dialog.permalink_dialog import PermalinkDialog
        dialog = PermalinkDialog()
        result = await async_dialog.execute_dialog(dialog)
        if result == QtWidgets.QDialog.Accepted:
            permalink = dialog.get_permalink_from_field()
            await self.generate_seed_from_permalink(permalink)

    def _import_spoiler_log(self):
        json_path = common_qt_lib.prompt_user_for_input_game_log(self)
        if json_path is not None:
            layout = LayoutDescription.from_file(json_path)
            self.open_game_details(layout)

    @asyncSlot()
    async def _browse_racetime(self):
        from randovania.gui.dialog.racetime_browser_dialog import RacetimeBrowserDialog
        dialog = RacetimeBrowserDialog()
        if not await dialog.refresh():
            return
        result = await async_dialog.execute_dialog(dialog)
        if result == QtWidgets.QDialog.Accepted:
            await self.generate_seed_from_permalink(dialog.permalink)

    def open_game_details(self, layout: LayoutDescription):
        self.GameDetailsSignal.emit(layout)

    def _open_game_details(self, layout: LayoutDescription):
        from randovania.gui.game_details.game_details_window import GameDetailsWindow
        details_window = GameDetailsWindow(self, self._options)
        details_window.update_layout_description(layout)
        details_window.show()
        self.track_window(details_window)

    # Releases info
    async def request_new_data(self):
        from randovania.interface_common import github_releases_data
        await self._on_releases_data(await github_releases_data.get_releases())

    async def _on_releases_data(self, releases: Optional[List[dict]]):
        current_version = update_checker.strict_current_version()
        last_changelog = self._options.last_changelog_displayed

        all_change_logs, new_change_logs, version_to_display = update_checker.versions_to_display_for_releases(
            current_version, last_changelog, releases)

        if version_to_display is not None:
            self.display_new_version(version_to_display)

        if all_change_logs:
            from randovania.gui.widgets.changelog_widget import ChangeLogWidget
            changelog_tab = ChangeLogWidget(all_change_logs)
            self.main_tab_widget.addTab(changelog_tab, "Change Log")

        if new_change_logs:
            from randovania.gui.lib.scroll_message_box import ScrollMessageBox

            message_box = ScrollMessageBox.create_new(
                self, QtWidgets.QMessageBox.Information,
                "What's new", "\n".join(new_change_logs),
                QtWidgets.QMessageBox.Ok,
            )
            message_box.label.setTextFormat(QtCore.Qt.TextFormat.MarkdownText)
            message_box.scroll_area.setMinimumSize(500, 300)
            await async_dialog.execute_dialog(message_box)

            with self._options as options:
                options.last_changelog_displayed = current_version

    def display_new_version(self, version: update_checker.VersionDescription):
        if self.menu_new_version is None:
            self.menu_new_version = QtGui.QAction("", self)
            self.menu_new_version.triggered.connect(self.open_version_link)
            self.menu_bar.addAction(self.menu_new_version)

        self.menu_new_version.setText("New version available: {}".format(version.tag_name))
        self._current_version_url = version.html_url

    def open_version_link(self):
        if self._current_version_url is None:
            raise RuntimeError("Called open_version_link, but _current_version_url is None")

        QtGui.QDesktopServices.openUrl(QUrl(self._current_version_url))

    # Options
    def on_options_changed(self):
        self.menu_action_validate_seed_after.setChecked(self._options.advanced_validate_seed_after)
        self.menu_action_timeout_generation_after_a_time_limit.setChecked(
            self._options.advanced_timeout_during_generation)
        self.menu_action_dark_mode.setChecked(self._options.dark_mode)

        self.menu_action_experimental_games.setChecked(self._options.experimental_games)
        self.refresh_game_list()

        self.generate_seed_tab.on_options_changed(self._options)
        theme.set_dark_theme(self._options.dark_mode)

    # Menu Actions
    def _open_data_visualizer_for_game(self, game: RandovaniaGame):
        self.open_data_visualizer_at(None, None, game)

    def open_data_visualizer_at(self,
                                world_name: Optional[str],
                                area_name: Optional[str],
                                game: RandovaniaGame = RandovaniaGame.METROID_PRIME_ECHOES,
                                ):
        from randovania.gui.data_editor import DataEditorWindow
        data_visualizer = DataEditorWindow.open_internal_data(game, False)
        self._data_visualizer = data_visualizer

        if world_name is not None:
            data_visualizer.focus_on_world_by_name(world_name)

        if area_name is not None:
            data_visualizer.focus_on_area_by_name(area_name)

        self._data_visualizer.show()

    def _open_data_editor_for_game(self, game: RandovaniaGame):
        from randovania.gui.data_editor import DataEditorWindow
        self._data_editor = DataEditorWindow.open_internal_data(game, True)
        self._data_editor.show()

    def _open_data_editor_prompt(self):
        from randovania.gui.data_editor import DataEditorWindow

        database_path = common_qt_lib.prompt_user_for_database_file(self)
        if database_path is None:
            return

        with database_path.open("r") as database_file:
            self._data_editor = DataEditorWindow(json.load(database_file), database_path, False, True)
            self._data_editor.show()

    async def open_map_tracker(self, configuration: "Preset"):
        from randovania.gui.tracker_window import TrackerWindow, InvalidLayoutForTracker

        try:
            self._map_tracker = await TrackerWindow.create_new(self._options.tracker_files_path, configuration)
        except InvalidLayoutForTracker as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Unsupported configuration for Tracker",
                str(e)
            )
            return

        self._map_tracker.show()

    # Difficulties stuff

    def _exec_trick_details(self, popup: "TrickDetailsPopup"):
        self._trick_details_popup = popup
        self._trick_details_popup.setWindowModality(Qt.WindowModal)
        self._trick_details_popup.open()

    def _open_trick_details_popup(self, game, trick: TrickResourceInfo, level: LayoutTrickLevel):
        from randovania.gui.dialog.trick_details_popup import TrickDetailsPopup
        self._exec_trick_details(TrickDetailsPopup(self, self, game, trick, level))

    def _setup_trick_difficulties_menu_on_show(self, menu: QtWidgets.QMenu, game: RandovaniaGame):
        def on_show():
            menu.aboutToShow.disconnect(on_show)
            self._setup_difficulties_menu(game, menu)

        menu.aboutToShow.connect(on_show)

    def _setup_difficulties_menu(self, game: RandovaniaGame, menu: QtWidgets.QMenu):
        from randovania.game_description import default_database
        game = default_database.game_description_for(game)
        tricks_in_use = used_tricks(game)

        menu.clear()
        for trick in sorted(game.resource_database.trick, key=lambda _trick: _trick.long_name):
            if trick not in tricks_in_use:
                continue

            trick_menu = QtWidgets.QMenu(self)
            trick_menu.setTitle(_t(trick.long_name))
            menu.addAction(trick_menu.menuAction())

            used_difficulties = difficulties_for_trick(game, trick)
            for trick_level in enum_lib.iterate_enum(LayoutTrickLevel):
                if trick_level in used_difficulties:
                    difficulty_action = QtGui.QAction(self)
                    difficulty_action.setText(trick_level.long_name)
                    trick_menu.addAction(difficulty_action)
                    difficulty_action.triggered.connect(
                        functools.partial(self._open_trick_details_popup, game, trick, trick_level))

    # ==========

    @asyncSlot()
    async def _on_validate_seed_change(self):
        old_value = self._options.advanced_validate_seed_after
        new_value = self.menu_action_validate_seed_after.isChecked()

        if old_value and not new_value:
            box = QtWidgets.QMessageBox(self)
            box.setWindowTitle("Disable validation?")
            box.setText(_DISABLE_VALIDATION_WARNING)
            box.setIcon(QtWidgets.QMessageBox.Warning)
            box.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            box.setDefaultButton(QtWidgets.QMessageBox.No)
            user_response = await async_dialog.execute_dialog(box)
            if user_response != QtWidgets.QMessageBox.Yes:
                self.menu_action_validate_seed_after.setChecked(True)
                return

        with self._options as options:
            options.advanced_validate_seed_after = new_value

    def _on_generate_time_limit_change(self):
        is_checked = self.menu_action_timeout_generation_after_a_time_limit.isChecked()
        with self._options as options:
            options.advanced_timeout_during_generation = is_checked

    def _on_menu_action_dark_mode(self):
        with self._options as options:
            options.dark_mode = self.menu_action_dark_mode.isChecked()

    def _on_menu_action_experimental_games(self):
        with self._options as options:
            options.experimental_games = self.menu_action_experimental_games.isChecked()

    def _open_auto_tracker(self):
        from randovania.gui.auto_tracker_window import AutoTrackerWindow
        self.auto_tracker_window = AutoTrackerWindow(common_qt_lib.get_game_connection(), self._options)
        self.auto_tracker_window.show()

    def _on_menu_action_previously_generated_games(self):
        path = self._options.game_history_path
        try:
            open_directory_in_explorer(path)

        except OSError:
            box = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Information, "Game History",
                                        f"Previously generated games can be found at:\n{path}",
                                        QtWidgets.QMessageBox.Ok, self)
            box.setTextInteractionFlags(Qt.TextSelectableByMouse)
            box.show()

    def _on_menu_action_log_files_directory(self):
        path = self._options.logs_path
        try:
            open_directory_in_explorer(path)

        except OSError:
            box = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Information, "Logs",
                                        f"Randovania logs can be found at:\n{path}",
                                        QtWidgets.QMessageBox.Ok, self)
            box.setTextInteractionFlags(Qt.TextSelectableByMouse)
            box.show()

    def _on_menu_action_layout_editor(self):
        from randovania.gui.corruption_layout_editor import CorruptionLayoutEditor
        self.corruption_editor = CorruptionLayoutEditor()
        self.corruption_editor.show()

    def setup_about_text(self):
        ABOUT_TEXT = "\n".join([
            "# Randovania",
            "",
            "<https://github.com/randovania/randovania>",
            "",
            "This software is covered by the [GNU General Public License v3 (GPLv3)](https://www.gnu.org/licenses/gpl-3.0.en.html)",
            "",
            "{community}",
            "",
            "{credits}",
        ])

        about_document: QtGui.QTextDocument = self.about_text_browser.document()

        # Populate from README.md
        community = get_readme_section("COMMUNITY")
        credit = get_readme_section("CREDITS")
        about_document.setMarkdown(ABOUT_TEXT.format(community=community, credits=credit))

        # Remove all hardcoded link color
        about_document.setHtml(about_document.toHtml().replace("color:#0000ff;", ""))
        cursor: QtGui.QTextCursor = self.about_text_browser.textCursor()
        cursor.setPosition(0)
        self.about_text_browser.setTextCursor(cursor)

    def setup_welcome_text(self):
        self.intro_label.setText(self.intro_label.text().format(version=VERSION))

        welcome = get_readme_section("WELCOME")
        supported = get_readme_section("SUPPORTED")
        experimental = get_readme_section("EXPERIMENTAL")

        self.games_supported_label.setText(supported)
        self.games_experimental_label.setText(experimental)
        self.intro_welcome_label.setText(welcome)


def get_readme_section(section: str) -> str:
    readme = get_readme().read_text()

    start_comment = f"<!-- Begin {section} -->\n"
    end_comment = f"<!-- End {section} -->"

    start = readme.find(start_comment) + len(start_comment)
    end = readme.find(end_comment)

    return readme[start:end]
