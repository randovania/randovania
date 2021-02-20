import functools
import json
import os
import platform
import subprocess
from functools import partial
from pathlib import Path
from typing import Optional, List

import markdown
from PySide2 import QtCore, QtWidgets, QtGui
from PySide2.QtCore import QUrl, Signal, Qt
from PySide2.QtGui import QDesktopServices
from PySide2.QtWidgets import QMainWindow, QAction, QMessageBox, QDialog, QMenu, QInputDialog
from asyncqt import asyncSlot

from randovania import VERSION
from randovania.game_description import default_database
from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.node import LogbookNode, LoreType
from randovania.game_description.resources.trick_resource_info import TrickResourceInfo
from randovania.games.game import RandovaniaGame
from randovania.gui.data_editor import DataEditorWindow
from randovania.gui.dialog.login_prompt_dialog import LoginPromptDialog
from randovania.gui.dialog.permalink_dialog import PermalinkDialog
from randovania.gui.dialog.trick_details_popup import TrickDetailsPopup
from randovania.gui.game_session_window import GameSessionWindow
from randovania.gui.generate_seed_tab import GenerateSeedTab
from randovania.gui.generated.main_window_ui import Ui_MainWindow
from randovania.gui.lib import common_qt_lib, async_dialog, theme
from randovania.gui.lib.qt_network_client import handle_network_errors, QtNetworkClient
from randovania.gui.lib.trick_lib import used_tricks, difficulties_for_trick
from randovania.gui.lib.window_manager import WindowManager
from randovania.gui.online_game_list_window import GameSessionBrowserDialog
from randovania.gui.tracker_window import TrackerWindow, InvalidLayoutForTracker
from randovania.interface_common import github_releases_data, update_checker
from randovania.interface_common.enum_lib import iterate_enum
from randovania.interface_common.options import Options
from randovania.interface_common.preset_manager import PresetManager
from randovania.layout.echoes_configuration import EchoesConfiguration
from randovania.layout.layout_description import LayoutDescription
from randovania.layout.trick_level import LayoutTrickLevel
from randovania.network_client.network_client import ConnectionState
from randovania.resolver import debug

_DISABLE_VALIDATION_WARNING = """
<html><head/><body>
<p>While it sometimes throws errors, the validation is what guarantees that your seed is completable.<br/>
Do <span style=" font-weight:600;">not</span> disable if you're uncomfortable with possibly unbeatable seeds.
</p><p align="center">Are you sure you want to disable validation?</p></body></html>
"""


class MainWindow(WindowManager, Ui_MainWindow):
    newer_version_signal = Signal(str, str)
    options_changed_signal = Signal()
    _is_preview_mode: bool = False

    menu_new_version: Optional[QAction] = None
    _current_version_url: Optional[str] = None
    _options: Options
    _data_visualizer: Optional[DataEditorWindow] = None
    _map_tracker: TrackerWindow
    _preset_manager: PresetManager
    game_session_window: Optional[GameSessionWindow] = None
    _login_window: Optional[QDialog] = None
    GameDetailsSignal = Signal(LayoutDescription)

    @property
    def _tab_widget(self):
        return self.main_tab_widget

    @property
    def preset_manager(self) -> PresetManager:
        return self._preset_manager

    @property
    def main_window(self) -> QMainWindow:
        return self

    @property
    def is_preview_mode(self) -> bool:
        return self._is_preview_mode

    def __init__(self, options: Options, preset_manager: PresetManager,
                 network_client: QtNetworkClient, preview: bool):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("Randovania {}".format(VERSION))
        self._is_preview_mode = preview
        self.setAcceptDrops(True)
        common_qt_lib.set_default_window_icon(self)

        # Remove all hardcoded link color
        about_document: QtGui.QTextDocument = self.about_text_browser.document()
        about_document.setHtml(about_document.toHtml().replace("color:#0000ff;", ""))
        self.browse_racetime_label.setText(self.browse_racetime_label.text().replace("color:#0000ff;", ""))

        self.intro_label.setText(self.intro_label.text().format(version=VERSION))

        self._preset_manager = preset_manager
        self.network_client = network_client

        if preview:
            debug.set_level(2)

        # Signals
        self.newer_version_signal.connect(self.display_new_version)
        self.options_changed_signal.connect(self.on_options_changed)
        self.GameDetailsSignal.connect(self._open_game_details)

        self.intro_play_now_button.clicked.connect(lambda: self.welcome_tab_widget.setCurrentWidget(self.tab_play))
        self.open_faq_button.clicked.connect(self._open_faq)
        self.open_database_viewer_button.clicked.connect(partial(self._open_data_visualizer_for_game,
                                                                 RandovaniaGame.PRIME2))

        self.import_permalink_button.clicked.connect(self._import_permalink)
        self.import_game_file_button.clicked.connect(self._import_spoiler_log)
        self.browse_racetime_button.clicked.connect(self._browse_racetime)
        self.browse_sessions_button.clicked.connect(self._browse_for_game_session)
        self.host_new_game_button.clicked.connect(self._host_game_session)
        self.create_new_seed_button.clicked.connect(
            lambda: self.welcome_tab_widget.setCurrentWidget(self.tab_create_seed))

        # Menu Bar
        for action, game in ((self.menu_action_prime_1_data_visualizer, RandovaniaGame.PRIME1),
                             (self.menu_action_prime_2_data_visualizer, RandovaniaGame.PRIME2),
                             (self.menu_action_prime_3_data_visualizer, RandovaniaGame.PRIME3)):
            action.triggered.connect(partial(self._open_data_visualizer_for_game, game))

        for action, game in ((self.menu_action_edit_prime_1, RandovaniaGame.PRIME1),
                             (self.menu_action_edit_prime_2, RandovaniaGame.PRIME2),
                             (self.menu_action_edit_prime_3, RandovaniaGame.PRIME3)):
            action.triggered.connect(partial(self._open_data_editor_for_game, game))

        self.menu_action_item_tracker.triggered.connect(self._open_item_tracker)
        self.menu_action_map_tracker.triggered.connect(self._on_menu_action_map_tracker)
        self.menu_action_edit_existing_database.triggered.connect(self._open_data_editor_prompt)
        self.menu_action_validate_seed_after.triggered.connect(self._on_validate_seed_change)
        self.menu_action_timeout_generation_after_a_time_limit.triggered.connect(self._on_generate_time_limit_change)
        self.menu_action_dark_mode.triggered.connect(self._on_menu_action_dark_mode)
        self.menu_action_open_auto_tracker.triggered.connect(self._open_auto_tracker)
        self.menu_action_previously_generated_games.triggered.connect(self._on_menu_action_previously_generated_games)
        self.menu_action_layout_editor.triggered.connect(self._on_menu_action_layout_editor)
        self.action_login_window.triggered.connect(self._action_login_window)

        self.menu_prime_1_trick_details.aboutToShow.connect(self._create_trick_details_prime_1)
        self.menu_prime_2_trick_details.aboutToShow.connect(self._create_trick_details_prime_2)
        self.menu_prime_3_trick_details.aboutToShow.connect(self._create_trick_details_prime_3)

        self.generate_seed_tab = GenerateSeedTab(self, self, options)
        self.generate_seed_tab.setup_ui()

        # Setting this event only now, so all options changed trigger only once
        options.on_options_changed = self.options_changed_signal.emit
        self._options = options
        with options:
            self.on_options_changed()

        self.main_tab_widget.setCurrentIndex(0)

        # Update hints text
        self._update_hints_text()

    def closeEvent(self, event):
        self.generate_seed_tab.stop_background_process()
        super().closeEvent(event)

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent):
        from randovania.layout.preset_migration import VersionedPreset

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
        from randovania.layout.preset_migration import VersionedPreset

        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.suffix == f".{LayoutDescription.file_extension()}":
                self.open_game_details(LayoutDescription.from_file(path))
                return

            elif path.suffix == f".{VersionedPreset.file_extension()}":
                self.main_tab_widget.setCurrentWidget(self.welcome_tab)
                self.welcome_tab_widget.setCurrentWidget(self.tab_create_seed)
                self.generate_seed_tab.import_preset_file(path)
                return

    # Generate Seed
    def _open_faq(self):
        self.main_tab_widget.setCurrentWidget(self.help_tab)
        self.help_tab_widget.setCurrentWidget(self.tab_faq)

    async def generate_seed_from_permalink(self, permalink):
        from randovania.interface_common.status_update_lib import ProgressUpdateCallable
        from randovania.gui.dialog.background_process_dialog import BackgroundProcessDialog

        def work(progress_update: ProgressUpdateCallable):
            from randovania.interface_common import simplified_patcher
            layout = simplified_patcher.generate_layout(progress_update=progress_update,
                                                        permalink=permalink,
                                                        options=self._options)
            progress_update(f"Success! (Seed hash: {layout.shareable_hash})", 1)
            return layout

        new_layout = await BackgroundProcessDialog.open_for_background_task(work, "Creating a game...")
        self.open_game_details(new_layout)

    @asyncSlot()
    async def _import_permalink(self):
        dialog = PermalinkDialog()
        result = await async_dialog.execute_dialog(dialog)
        if result == QDialog.Accepted:
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
        if result == QDialog.Accepted:
            await self.generate_seed_from_permalink(dialog.permalink)

    async def _game_session_active(self) -> bool:
        if self.game_session_window is None or self.game_session_window.has_closed:
            return False
        else:
            await async_dialog.message_box(
                self,
                QtWidgets.QMessageBox.Critical,
                "Game Session in progress",
                "There's already a game session window open. Please close it first.",
                QMessageBox.Ok
            )
            self.game_session_window.activateWindow()
            return True

    async def _ensure_logged_in(self) -> bool:
        network_client = self.network_client
        if network_client.connection_state == ConnectionState.Connected:
            return True

        if network_client.connection_state.is_disconnected:
            message_box = QtWidgets.QMessageBox(QtWidgets.QMessageBox.NoIcon, "Connecting",
                                                "Connecting to server...", QtWidgets.QMessageBox.Cancel,
                                                self)

            connecting = network_client.connect_to_server()
            message_box.rejected.connect(connecting.cancel)
            message_box.show()
            try:
                await connecting
            finally:
                message_box.close()

        if network_client.current_user is None:
            await async_dialog.execute_dialog(LoginPromptDialog(network_client))

        return network_client.current_user is not None

    @asyncSlot()
    @handle_network_errors
    async def _browse_for_game_session(self):
        if await self._game_session_active():
            return

        if not await self._ensure_logged_in():
            return

        network_client = self.network_client
        browser = GameSessionBrowserDialog(network_client)
        await browser.refresh()
        if await async_dialog.execute_dialog(browser) == browser.Accepted:
            self.game_session_window = await GameSessionWindow.create_and_update(
                network_client, common_qt_lib.get_game_connection(), self.preset_manager,
                self, self._options)
            if self.game_session_window is not None:
                self.game_session_window.show()

    @asyncSlot()
    @handle_network_errors
    async def _action_login_window(self):
        if self._login_window is not None:
            return self._login_window.show()

        self._login_window = LoginPromptDialog(self.network_client)
        try:
            await async_dialog.execute_dialog(self._login_window)
        finally:
            self._login_window = None

    @asyncSlot()
    @handle_network_errors
    async def _host_game_session(self):
        if await self._game_session_active():
            return

        if not await self._ensure_logged_in():
            return

        dialog = QInputDialog(self)
        dialog.setModal(True)
        dialog.setWindowTitle("Enter session name")
        dialog.setLabelText("Select a name for the session:")
        if await async_dialog.execute_dialog(dialog) != dialog.Accepted:
            return

        await self.network_client.create_new_session(dialog.textValue())
        self.game_session_window = await GameSessionWindow.create_and_update(self.network_client,
                                                                             common_qt_lib.get_game_connection(),
                                                                             self.preset_manager, self, self._options)
        if self.game_session_window is not None:
            self.game_session_window.show()

    def open_game_details(self, layout: LayoutDescription):
        self.GameDetailsSignal.emit(layout)

    def _open_game_details(self, layout: LayoutDescription):
        from randovania.gui.seed_details_window import SeedDetailsWindow
        details_window = SeedDetailsWindow(self, self._options)
        details_window.update_layout_description(layout)
        details_window.show()
        self.track_window(details_window)

    # Releases info
    async def request_new_data(self):
        await self._on_releases_data(await github_releases_data.get_releases())

    async def _on_releases_data(self, releases: Optional[List[dict]]):
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
            changelog_tab_layout.setContentsMargins(0, 0, 0, 0)
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
            changelog_label.setWordWrap(True)
            changelog_scroll_layout.addWidget(changelog_label)
            changelog_scroll_area.setWidget(changelog_scroll_contents)
            changelog_tab_layout.addWidget(changelog_scroll_area)
            self.help_tab_widget.addTab(changelog_tab, "Change Log")

        if new_change_logs:
            await async_dialog.message_box(self, QtWidgets.QMessageBox.Information,
                                           "What's new", markdown.markdown("\n".join(new_change_logs)))
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
        self.menu_action_validate_seed_after.setChecked(self._options.advanced_validate_seed_after)
        self.menu_action_timeout_generation_after_a_time_limit.setChecked(
            self._options.advanced_timeout_during_generation)
        self.menu_action_dark_mode.setChecked(self._options.dark_mode)

        self.generate_seed_tab.on_options_changed(self._options)
        theme.set_dark_theme(self._options.dark_mode)

    # Menu Actions
    def _open_data_visualizer_for_game(self, game: RandovaniaGame):
        self.open_data_visualizer_at(None, None, game)

    def open_data_visualizer_at(self,
                                world_name: Optional[str],
                                area_name: Optional[str],
                                game: RandovaniaGame = RandovaniaGame.PRIME2,
                                ):
        self._data_visualizer = DataEditorWindow.open_internal_data(game, False)

        if world_name is not None:
            self._data_visualizer.focus_on_world(world_name)

        if area_name is not None:
            self._data_visualizer.focus_on_area(area_name)

        self._data_visualizer.show()

    def _open_data_editor_for_game(self, game: RandovaniaGame):
        self._data_editor = DataEditorWindow.open_internal_data(game, True)
        self._data_editor.show()

    def _open_data_editor_prompt(self):
        database_path = common_qt_lib.prompt_user_for_database_file(self)
        if database_path is None:
            return

        with database_path.open("r") as database_file:
            self._data_editor = DataEditorWindow(json.load(database_file), database_path, False, True)
            self._data_editor.show()

    @asyncSlot()
    async def _on_menu_action_map_tracker(self):
        dialog = QtWidgets.QInputDialog(self)
        dialog.setWindowTitle("Map Tracker")
        dialog.setLabelText("Select preset used for the tracker.")
        dialog.setComboBoxItems([preset.name for preset in self._preset_manager.all_presets])
        dialog.setTextValue(self._options.selected_preset_name)
        result = await async_dialog.execute_dialog(dialog)
        if result == QtWidgets.QDialog.Accepted:
            preset = self._preset_manager.preset_for_name(dialog.textValue())
            self.open_map_tracker(preset.get_preset().configuration)

    def open_map_tracker(self, configuration: EchoesConfiguration):
        try:
            self._map_tracker = TrackerWindow(self._options.tracker_files_path, configuration)
        except InvalidLayoutForTracker as e:
            QMessageBox.critical(
                self,
                "Unsupported configuration for Tracker",
                str(e)
            )
            return

        self._map_tracker.show()

    def _open_item_tracker(self):
        # Importing this at root level seems to crash linux tests :(
        from PySide2.QtWebEngineWidgets import QWebEngineView

        tracker_window = QMainWindow()
        tracker_window.setWindowTitle("Item Tracker")
        tracker_window.resize(370, 380)

        web_view = QWebEngineView(tracker_window)
        tracker_window.setCentralWidget(web_view)

        self.web_view = web_view

        def update_window_icon():
            tracker_window.setWindowIcon(web_view.icon())

        web_view.iconChanged.connect(update_window_icon)
        web_view.load(QUrl("https://spaghettitoastbook.github.io/echoes/tracker/"))

        tracker_window.show()
        self._item_tracker_window = tracker_window

    # Difficulties stuff

    def _exec_trick_details(self, popup: TrickDetailsPopup):
        self._trick_details_popup = popup
        self._trick_details_popup.setWindowModality(Qt.WindowModal)
        self._trick_details_popup.open()

    def _open_trick_details_popup(self, game, trick: TrickResourceInfo, level: LayoutTrickLevel):
        self._exec_trick_details(TrickDetailsPopup(self, self, game, trick, level))

    def _create_trick_details_prime_1(self):
        self.menu_prime_1_trick_details.aboutToShow.disconnect(self._create_trick_details_prime_1)
        self._setup_difficulties_menu(RandovaniaGame.PRIME1, self.menu_prime_1_trick_details)

    def _create_trick_details_prime_2(self):
        self.menu_prime_2_trick_details.aboutToShow.disconnect(self._create_trick_details_prime_2)
        self._setup_difficulties_menu(RandovaniaGame.PRIME2, self.menu_prime_2_trick_details)

    def _create_trick_details_prime_3(self):
        self.menu_prime_3_trick_details.aboutToShow.disconnect(self._create_trick_details_prime_3)
        self._setup_difficulties_menu(RandovaniaGame.PRIME3, self.menu_prime_3_trick_details)

    def _setup_difficulties_menu(self, game: RandovaniaGame, menu: QtWidgets.QMenu):
        game = default_database.game_description_for(game)
        tricks_in_use = used_tricks(game)

        menu.clear()
        for trick in sorted(game.resource_database.trick, key=lambda _trick: _trick.long_name):
            if trick not in tricks_in_use:
                continue

            trick_menu = QMenu(self)
            trick_menu.setTitle(trick.long_name)
            menu.addAction(trick_menu.menuAction())

            used_difficulties = difficulties_for_trick(game, trick)
            for i, trick_level in enumerate(iterate_enum(LayoutTrickLevel)):
                if trick_level in used_difficulties:
                    difficulty_action = QAction(self)
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
            box = QMessageBox(self)
            box.setWindowTitle("Disable validation?")
            box.setText(_DISABLE_VALIDATION_WARNING)
            box.setIcon(QMessageBox.Warning)
            box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            box.setDefaultButton(QMessageBox.No)
            user_response = await async_dialog.execute_dialog(box)
            if user_response != QMessageBox.Yes:
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

    def _open_auto_tracker(self):
        from randovania.gui.auto_tracker_window import AutoTrackerWindow
        self.auto_tracker_window = AutoTrackerWindow(common_qt_lib.get_game_connection(), self._options)
        self.auto_tracker_window.show()

    def _on_menu_action_previously_generated_games(self):
        path = self._options.data_dir.joinpath("game_history")
        try:
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":
                subprocess.run(["open", path])
            else:
                subprocess.run(["xdg-open", path])
        except OSError:
            print("Exception thrown :)")
            box = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Information, "Game History",
                                        f"Previously generated games can be found at:\n{path}",
                                        QtWidgets.QMessageBox.Ok, self)
            box.setTextInteractionFlags(Qt.TextSelectableByMouse)
            box.show()

    def _on_menu_action_layout_editor(self):
        from randovania.gui.corruption_layout_editor import CorruptionLayoutEditor
        self.corruption_editor = CorruptionLayoutEditor()
        self.corruption_editor.show()

    def _update_hints_text(self):
        game_description = default_database.default_prime2_game_description()
        item_database = default_database.default_prime2_item_database()

        rows = []

        for item in item_database.major_items.values():
            rows.append((
                item.name,
                item.item_category.hint_details[1],
                item.item_category.general_details[1],
                item.broad_category.hint_details[1],
            ))

        from randovania.games.prime.echoes_items import DARK_TEMPLE_KEY_NAMES
        for dark_temple_key in DARK_TEMPLE_KEY_NAMES:
            rows.append((
                dark_temple_key.format("").strip(),
                ItemCategory.TEMPLE_KEY.hint_details[1],
                ItemCategory.TEMPLE_KEY.general_details[1],
                ItemCategory.KEY.hint_details[1],
            ))

        rows.append((
            "Sky Temple Key",
            ItemCategory.SKY_TEMPLE_KEY.hint_details[1],
            ItemCategory.SKY_TEMPLE_KEY.general_details[1],
            ItemCategory.KEY.hint_details[1],
        ))

        for item in item_database.ammo.values():
            rows.append((
                item.name,
                ItemCategory.EXPANSION.hint_details[1],
                ItemCategory.EXPANSION.general_details[1],
                item.broad_category.hint_details[1],
            ))

        self.hint_item_names_tree_widget.setRowCount(len(rows))
        for i, elements in enumerate(rows):
            for j, element in enumerate(elements):
                self.hint_item_names_tree_widget.setItem(i, j, QtWidgets.QTableWidgetItem(element))

        for i in range(4):
            self.hint_item_names_tree_widget.resizeColumnToContents(i)

        number_for_hint_type = {
            hint_type: i + 1
            for i, hint_type in enumerate(LoreType)
        }
        used_hint_types = set()

        self.hint_tree_widget.setSortingEnabled(False)

        # TODO: This ignores the Dark World names. But there's currently no logbook nodes in Dark World.
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
