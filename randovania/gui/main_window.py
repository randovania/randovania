from __future__ import annotations

import asyncio
import base64
import functools
import logging
import os
import platform
import re
import typing
from functools import partial
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, QUrl, Signal
from qasync import asyncSlot

import randovania
from randovania import VERSION, get_readme_section, monitoring
from randovania.games.game import RandovaniaGame
from randovania.gui.generated.main_window_ui import Ui_MainWindow
from randovania.gui.lib import async_dialog, common_qt_lib, theme
from randovania.gui.lib.background_task_mixin import BackgroundTaskMixin
from randovania.gui.lib.window_manager import WindowManager
from randovania.interface_common import update_checker
from randovania.interface_common.installation_check import find_bad_installation
from randovania.layout.base.trick_level import LayoutTrickLevel
from randovania.layout.layout_description import LayoutDescription
from randovania.lib import enum_lib, json_lib
from randovania.resolver import debug

if typing.TYPE_CHECKING:
    from randovania.game_description.resources.trick_resource_info import TrickResourceInfo
    from randovania.gui.lib.qt_network_client import QtNetworkClient
    from randovania.gui.multiplayer_session_window import MultiplayerSessionWindow
    from randovania.gui.multiworld_client import MultiworldClient
    from randovania.gui.widgets.game_connection_window import GameConnectionWindow
    from randovania.interface_common.options import Options
    from randovania.interface_common.preset_manager import PresetManager
    from randovania.layout.base.trick_level_configuration import TrickLevelConfiguration
    from randovania.layout.permalink import Permalink
    from randovania.layout.preset import Preset
    from randovania.lib.status_update_lib import ProgressUpdateCallable

_DISABLE_VALIDATION_WARNING = """
<html><head/><body>
<p>While it sometimes throws errors, the validation is what guarantees that your seed is completable.<br/>
Do <span style=" font-weight:600;">not</span> disable if you're uncomfortable with possibly unbeatable seeds.
</p><p align="center">Are you sure you want to disable validation?</p></body></html>
"""

_ANOTHER_PROCESS_GENERATION_WARNING = """
<html><head/><body>
<p>Generation by default runs in another process to keep Randovania responsive while it happens.<br/>
Running in the same process as the user interface is a good troubleshooting step if you're having issues.

</p><p align="center">Do you want to continue?</p></body></html>
"""


def _t(key: str, disambiguation: str | None = None):
    return QtCore.QCoreApplication.translate("MainWindow", key, disambiguation)


class LayoutWithPlayers(typing.NamedTuple):
    layout: LayoutDescription
    players: list[str] | None


class GameQtElements(typing.NamedTuple):
    logo: QtWidgets.QLabel
    on_hover_effect: QtWidgets.QGraphicsColorizeEffect | None
    multi_banner: QtWidgets.QLabel
    color_effect: QtWidgets.QGraphicsColorizeEffect
    multi_icon: QtWidgets.QLabel
    tile: QtWidgets.QStackedWidget


class MainWindow(WindowManager, BackgroundTaskMixin, Ui_MainWindow):
    options_changed_signal = Signal()
    _is_preview_mode: bool = False

    menu_new_version: QtGui.QAction | None = None
    _current_version_url: str | None = None
    _options: Options
    _data_visualizer: QtWidgets.QWidget | None = None
    _map_tracker: QtWidgets.QWidget
    _preset_manager: PresetManager
    _multiworld_client: MultiworldClient
    _play_game_elements: dict[RandovaniaGame, GameQtElements]
    about_window: QtWidgets.QMainWindow | None = None
    dependencies_window: QtWidgets.QMainWindow | None = None
    reporting_widget: QtWidgets.QWidget | None = None
    all_change_logs: dict[str, str] | None = None
    changelog_tab: QtWidgets.QWidget | None = None
    changelog_window: QtWidgets.QMainWindow | None = None
    help_window: QtWidgets.QMainWindow | None = None
    game_connection_window: GameConnectionWindow | None = None
    opened_session_windows: dict[int, MultiplayerSessionWindow]

    GameDetailsSignal = Signal(LayoutWithPlayers)
    RequestOpenLayoutSignal = Signal(Path)
    InitPostShowSignal = Signal()
    InitPostShowCompleteSignal = Signal()

    @property
    def _tab_widget(self):
        return self.main_tab_widget

    @property
    def preset_manager(self) -> PresetManager:
        return self._preset_manager

    @property
    def multiworld_client(self):
        return self._multiworld_client

    @property
    def main_window(self) -> QtWidgets.QMainWindow:
        return self

    @property
    def is_preview_mode(self) -> bool:
        return self._is_preview_mode

    def __init__(
        self,
        options: Options,
        preset_manager: PresetManager,
        network_client: QtNetworkClient,
        multiworld_client: MultiworldClient,
        preview: bool,
    ):
        monitoring.metrics.incr("gui_rdv_started")

        super().__init__()
        self.setupUi(self)
        self.setWindowTitle(f"Randovania {VERSION}")
        self._is_preview_mode = preview
        self.setAcceptDrops(True)
        common_qt_lib.set_default_window_icon(self)

        self.setup_welcome_text()
        self.browse_racetime_label.setText(self.browse_racetime_label.text().replace("color:#0000ff;", ""))

        self._preset_manager = preset_manager
        self.network_client = network_client
        self._multiworld_client = multiworld_client
        self._play_game_elements = {}
        self.opened_session_windows = {}

        if preview:
            debug.set_level(2)

        if randovania.is_frozen():
            self.menu_bar.removeAction(self.menu_edit.menuAction())

        # Signals
        self.options_changed_signal.connect(self.on_options_changed)
        self.GameDetailsSignal.connect(self._open_game_details)
        self.RequestOpenLayoutSignal.connect(self._request_open_layout)
        self.InitPostShowSignal.connect(self.initialize_post_show)
        self.main_tab_widget.currentChanged.connect(self._on_main_tab_changed)

        self.intro_play_solo_button.clicked.connect(partial(self._set_main_tab, self.tab_game_list))
        self.intro_play_existing_button.clicked.connect(partial(self._set_main_tab, self.tab_play_existing))
        self.intro_play_multiworld_button.clicked.connect(partial(self._set_main_tab, self.tab_multiworld))

        self.import_permalink_button.clicked.connect(self._import_permalink)
        self.import_game_file_button.clicked.connect(self._import_spoiler_log)
        self.browse_racetime_button.clicked.connect(self._browse_racetime)

        self.background_tasks_button_lock_signal.connect(self.enable_buttons_with_background_tasks)
        self.progress_update_signal.connect(self.update_progress)
        self.stop_background_process_button.clicked.connect(self.stop_background_process)

        self.multiworld_intro_label.linkActivated.connect(self.open_app_navigation_link)

        self.set_games_selector_visible(True)

        # Menu Bar
        self.game_menus = []
        self.menu_action_edits = []

        from randovania.gui.lib.clickable_label import ClickableLabel
        from randovania.gui.lib.flow_layout import FlowLayout

        self.play_flow_layout = FlowLayout(self.game_list_contents, True)
        self.play_flow_layout.setSpacing(15)
        self.play_flow_layout.setAlignment(Qt.AlignHCenter)

        banner_img_path = randovania.get_data_path().joinpath("gui_assets", "common", "banner.png")
        multiworld_img_path = randovania.get_data_path().joinpath("gui_assets", "common", "multiworld.png")
        bannerSize = 40

        for game in RandovaniaGame.sorted_all_games():
            # Play game buttons
            pack_tile = QtWidgets.QStackedWidget(self.game_list_contents)
            pack_tile.setFixedSize(150, 200)

            image_path = game.data_path.joinpath("assets", "cover.png")
            logo = ClickableLabel(pack_tile)
            logo.setPixmap(QtGui.QPixmap(os.fspath(image_path)))
            logo.setFrameStyle(QtWidgets.QFrame.Panel | QtWidgets.QFrame.Plain)
            logo.setScaledContents(True)
            logo.setFixedSize(150, 200)
            logo.setToolTip(game.long_name)
            logo.setAccessibleName(game.long_name)
            logo.clicked.connect(partial(self._select_game, game))
            logo.setVisible(game.data.development_state.can_view())

            on_hover_effect = QtWidgets.QGraphicsColorizeEffect()
            on_hover_effect.setStrength(0.5)
            logo.setGraphicsEffect(on_hover_effect)

            multi_banner = QtWidgets.QLabel(pack_tile)
            color_effect = QtWidgets.QGraphicsColorizeEffect(multi_banner)
            multi_icon = QtWidgets.QLabel(pack_tile)

            if game.data.defaults_available_in_game_sessions:
                multi_banner.setPixmap(QtGui.QPixmap(os.fspath(banner_img_path)))
                multi_banner.setScaledContents(True)
                multi_banner.setFixedSize(bannerSize, bannerSize)
                multi_banner.setGraphicsEffect(color_effect)
                multi_banner.move(0, 2)

                color_effect.setStrength(0.5)

                multi_icon.setPixmap(QtGui.QPixmap(os.fspath(multiworld_img_path)))
                multi_icon.setScaledContents(True)
                multi_icon.setFixedSize(int(bannerSize / 2), int(bannerSize / 2))
                multi_icon.move(int(bannerSize / 4), int(2 + bannerSize / 4))
                multi_icon.setToolTip(game.short_name + " is multiworld compatible.")
                multi_icon.setAccessibleName(game.long_name + " multiworld compatibility indicator")

            def highlight_logo(
                label_effect: QtWidgets.QGraphicsColorizeEffect,
                multi_banner_effect: QtWidgets.QGraphicsColorizeEffect,
                active: bool,
            ) -> None:
                label_effect.setEnabled(active)
                if active:
                    multi_banner_effect.setColor(QtGui.QColor(50, 250, 52))
                else:
                    multi_banner_effect.setColor(QtGui.QColor(70, 200, 80))

            highlight_logo(on_hover_effect, color_effect, False)

            logo.entered.connect(partial(highlight_logo, on_hover_effect, color_effect, True))
            logo.left.connect(partial(highlight_logo, on_hover_effect, color_effect, False))
            self.play_flow_layout.addWidget(pack_tile)
            self._play_game_elements[game] = GameQtElements(
                logo, on_hover_effect, multi_banner, color_effect, multi_icon, pack_tile
            )

            # Sub-Menu in Open Menu
            game_menu = QtWidgets.QMenu(self.menu_open)
            game_menu.setTitle(_t(game.long_name))
            game_menu.game = game

            if game.data.development_state.can_view():
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
        self.menu_action_generate_in_another_process.triggered.connect(self._on_generate_in_another_process_change)
        self.menu_action_dark_mode.triggered.connect(self._on_menu_action_dark_mode)
        self.menu_action_show_multiworld_banner.triggered.connect(self._on_menu_action_show_multiworld_banner)
        self.menu_action_experimental_settings.triggered.connect(self._on_menu_action_experimental_settings)
        self.menu_action_open_auto_tracker.triggered.connect(self._open_auto_tracker)
        self.menu_action_previously_generated_games.triggered.connect(self._on_menu_action_previously_generated_games)
        self.menu_action_log_files_directory.triggered.connect(self._on_menu_action_log_files_directory)
        self.menu_action_help.triggered.connect(self._on_menu_action_help)
        self.menu_action_verify_installation.triggered.connect(self._on_menu_action_verify_installation)
        self.menu_action_verify_installation.setVisible(randovania.is_frozen() and platform.system() == "Windows")
        self.menu_action_changelog.triggered.connect(self._on_menu_action_changelog)
        self.menu_action_changelog.setVisible(False)
        self.menu_action_about.triggered.connect(self._on_menu_action_about)
        self.menu_action_dependencies.triggered.connect(self._on_menu_action_dependencies)
        self.menu_action_automatic_reporting.triggered.connect(self._on_menu_action_automatic_reporting)

        # Setting this event only now, so all options changed trigger only once
        options.on_options_changed = self.options_changed_signal.emit
        self._options = options
        self.tab_game_details.set_main_window(self)
        self.refresh_game_list()

        self.main_tab_widget.setCurrentIndex(0)

    def closeEvent(self, event):
        self.stop_background_process()
        super().closeEvent(event)

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent):
        from randovania.layout.versioned_preset import VersionedPreset

        valid_extensions = [
            LayoutDescription.file_extension(),
            VersionedPreset.file_extension(),
        ]
        valid_extensions_with_dot = {f".{extension}" for extension in valid_extensions}

        for url in event.mimeData().urls():
            ext = Path(url.toLocalFile()).suffix
            if ext in valid_extensions_with_dot:
                event.acceptProposedAction()
                return

    def dropEvent(self, event: QtGui.QDropEvent):
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.suffix == f".{LayoutDescription.file_extension()}":
                self.RequestOpenLayoutSignal.emit(path)
                return

            # FIXME: re-implement importing presets
            # elif path.suffix == f".{VersionedPreset.file_extension()}":
            #     self._set_main_tab(self.tab_create_seed)
            #     self.tab_create_seed.import_preset_file(path)
            #     return

    def showEvent(self, event: QtGui.QShowEvent):
        self.InitPostShowSignal.emit()

    # Per-Game elements
    def refresh_game_list(self) -> None:
        for game, game_elements in self._play_game_elements.items():
            game_elements.tile.setVisible(game.data.development_state.can_view())
            game_elements.multi_banner.setVisible(self._options.show_multiworld_banner)
            game_elements.multi_icon.setVisible(self._options.show_multiworld_banner)

        for game_menu in self.game_menus:
            self.menu_open.removeAction(game_menu.menuAction())

        for game_menu, edit_action in zip(self.game_menus, self.menu_action_edits):
            game: RandovaniaGame = game_menu.game
            if game.data.development_state.can_view():
                self.menu_open.addAction(game_menu.menuAction())

    def _on_main_tab_changed(self):
        if self.main_tab_widget.currentWidget() not in {self.tab_game_list, self.tab_game_details}:
            self.set_games_selector_visible(True)

    def _set_main_tab(self, tab: QtWidgets.QWidget):
        self.main_tab_widget.setCurrentWidget(tab)

    def _set_main_tab_visible(self, tab: QtWidgets.QWidget, visible: bool):
        self.main_tab_widget.setTabVisible(self.main_tab_widget.indexOf(tab), visible)

    def set_games_selector_visible(self, visible: bool):
        tabs = [self.tab_game_list, self.tab_game_details]
        for tab in tabs:
            self._set_main_tab_visible(tab, True)

        currently_selected = self.main_tab_widget.currentWidget() in tabs
        if visible:
            if currently_selected:
                self._set_main_tab(self.tab_game_list)
            self._set_main_tab_visible(self.tab_game_details, False)
        else:
            if currently_selected:
                self._set_main_tab(self.tab_game_details)
            self._set_main_tab_visible(self.tab_game_list, False)

    def _select_game(self, game: RandovaniaGame):
        with monitoring.start_transaction(op="task", name="load_game_tab") as span:
            span.set_tag("game", game)
            span.set_tag("first_show", self.tab_game_details._first_show)
            # Set the game we want first, so we don't waste CPU creating wrong widgets
            self.tab_game_details.set_current_game(game)

            # Make sure the target tab is visible, but don't use set_games_selector_visible to
            # avoid hiding the current tab
            self.set_games_selector_visible(False)
            self._set_main_tab(self.tab_game_details)

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
        self.online_interactions = OnlineInteractions(
            self, self.preset_manager, self.network_client, self, self._options
        )
        self.game_connection_button.clicked.connect(self.open_game_connection_window)

        logging.info("Will update for modified options")
        with self._options:
            self.on_options_changed()

        self.InitPostShowCompleteSignal.emit()

    # Generate Seed
    async def generate_seed_from_permalink(self, permalink: Permalink):
        from randovania.gui.dialog.background_process_dialog import BackgroundProcessDialog

        def work(progress_update: ProgressUpdateCallable):
            from randovania.interface_common import generator_frontend

            layout = generator_frontend.generate_layout(
                progress_update=progress_update, parameters=permalink.parameters, options=self._options
            )
            progress_update(f"Success! (Seed hash: {layout.shareable_hash})", 1)
            return layout

        try:
            new_layout = await BackgroundProcessDialog.open_for_background_task(work, "Creating a game...")
        except asyncio.exceptions.CancelledError:
            return

        if permalink.seed_hash is not None and permalink.seed_hash != new_layout.shareable_hash_bytes:
            expected = base64.b32encode(permalink.seed_hash).decode()
            response = await async_dialog.warning(
                self,
                "Unexpected hash",
                f"Expected has to be {expected}. got {new_layout.shareable_hash}. Do you wish to continue?",
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            )
            if response != QtWidgets.QMessageBox.StandardButton.Yes:
                return

        self.open_game_details(new_layout)

    @asyncSlot()
    async def _import_permalink(self):
        monitoring.metrics.incr(key="gui_import_permalink_click_opened")
        from randovania.gui.dialog.permalink_dialog import PermalinkDialog

        dialog = PermalinkDialog()
        result = await async_dialog.execute_dialog(dialog)
        if result == QtWidgets.QDialog.DialogCode.Accepted:
            monitoring.metrics.incr(key="gui_import_permalink_click_accepted")
            permalink = dialog.get_permalink_from_field()
            await self.generate_seed_from_permalink(permalink)
        else:
            monitoring.metrics.incr(key="gui_import_permalink_click_cancelled")

    @asyncSlot()
    async def _import_spoiler_log(self):
        from randovania.gui.lib import layout_loader

        layout = await layout_loader.prompt_and_load_layout_description(self)
        if layout is not None:
            self.open_game_details(layout)

    @asyncSlot()
    async def _browse_racetime(self):
        monitoring.metrics.incr(key="gui_browse_racetime_opened")
        from randovania.gui.dialog.racetime_browser_dialog import RacetimeBrowserDialog

        dialog = RacetimeBrowserDialog()
        if not await dialog.refresh():
            return
        result = await async_dialog.execute_dialog(dialog)
        if result == QtWidgets.QDialog.DialogCode.Accepted:
            monitoring.metrics.incr(key="gui_browse_racetime_accepted")
            await self.generate_seed_from_permalink(dialog.permalink)
        else:
            monitoring.metrics.incr(key="gui_browse_racetime_cancelled")

    def open_game_details(self, layout: LayoutDescription, players: list[str] | None = None):
        self.GameDetailsSignal.emit(LayoutWithPlayers(layout, players))

    def _open_game_details(self, layout: LayoutWithPlayers):
        from randovania.gui.game_details.game_details_window import GameDetailsWindow

        details_window = GameDetailsWindow(self, self._options)
        details_window.update_layout_description(layout.layout, layout.players)
        details_window.show()
        self.track_window(details_window)

    @asyncSlot(Path)
    async def _request_open_layout(self, path: Path):
        from randovania.gui.lib import layout_loader

        layout = await layout_loader.load_layout_description(self, path)
        if layout is not None:
            self.open_game_details(layout)

    # Releases info
    async def request_new_data(self):
        from randovania.interface_common import github_releases_data

        await self._on_releases_data(await github_releases_data.get_releases())

    async def _on_releases_data(self, releases: list[dict] | None):
        current_version = update_checker.strict_current_version()
        last_changelog = self._options.last_changelog_displayed

        (all_change_logs, new_change_logs, version_to_display) = update_checker.versions_to_display_for_releases(
            current_version, last_changelog, releases
        )

        if version_to_display is not None:
            self.display_new_version(version_to_display)

        if all_change_logs:
            self.all_change_logs = all_change_logs
            self.menu_action_changelog.setVisible(True)

        if new_change_logs:
            from randovania.gui.lib.scroll_message_box import ScrollMessageBox

            message_box = ScrollMessageBox.create_new(
                self,
                QtWidgets.QMessageBox.Icon.Information,
                "What's new",
                "\n".join(new_change_logs),
                QtWidgets.QMessageBox.StandardButton.Ok,
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

        self.menu_new_version.setText(f"New version available: {version.tag_name}")
        self._current_version_url = version.html_url

    def open_version_link(self):
        if self._current_version_url is None:
            raise RuntimeError("Called open_version_link, but _current_version_url is None")

        QtGui.QDesktopServices.openUrl(QUrl(self._current_version_url))

    def open_game_connection_window(self):
        from randovania.gui.widgets.game_connection_window import GameConnectionWindow

        if self.game_connection_window is None:
            self.game_connection_window = GameConnectionWindow(
                self, self.network_client, self._options, common_qt_lib.get_game_connection()
            )

        self.game_connection_window.show()
        self.game_connection_window.raise_()

    # Options
    def on_options_changed(self):
        self.menu_action_validate_seed_after.setChecked(self._options.advanced_validate_seed_after)
        self.menu_action_timeout_generation_after_a_time_limit.setChecked(
            self._options.advanced_timeout_during_generation
        )
        self.menu_action_generate_in_another_process.setChecked(self._options.advanced_generate_in_another_process)
        self.menu_action_dark_mode.setChecked(self._options.dark_mode)
        self.menu_action_show_multiworld_banner.setChecked(self._options.show_multiworld_banner)
        self.menu_action_experimental_settings.setChecked(self._options.experimental_settings)

        self.tab_game_details.on_options_changed(self._options)
        self.refresh_game_list()
        theme.set_dark_theme(self._options.dark_mode)

        self.network_client.allow_reporting_username = self._options.use_user_for_crash_reporting

    # Menu Actions
    def _open_data_visualizer_for_game(self, game: RandovaniaGame):
        self.open_data_visualizer_at(None, None, game)

    def open_data_visualizer_at(
        self,
        region_name: str | None,
        area_name: str | None,
        game: RandovaniaGame,
        trick_levels: TrickLevelConfiguration | None = None,
    ):
        from randovania.gui.data_editor import DataEditorWindow

        data_visualizer = DataEditorWindow.open_internal_data(game, False)
        self._data_visualizer = data_visualizer

        if region_name is not None:
            data_visualizer.focus_on_region_by_name(region_name)

        if area_name is not None:
            data_visualizer.focus_on_area_by_name(area_name)

        if trick_levels is not None:
            data_visualizer.connection_filters.set_selected_tricks(trick_levels)

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

        self._data_editor = DataEditorWindow(json_lib.read_path(database_path), database_path, False, True)
        self._data_editor.show()

    async def open_map_tracker(self, configuration: Preset):
        from randovania.gui.tracker_window import InvalidLayoutForTracker, TrackerWindow

        try:
            self._map_tracker = await TrackerWindow.create_new(self._options.tracker_files_path, configuration)
        except InvalidLayoutForTracker as e:
            QtWidgets.QMessageBox.critical(self, "Unsupported configuration for Tracker", str(e))
            return

        self._map_tracker.show()

    # Difficulties stuff

    def _exec_trick_details(self, popup: QtWidgets.QDialog):
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
        from randovania.layout.lib import trick_lib

        game = default_database.game_description_for(game)
        tricks_in_use = trick_lib.used_tricks(game)

        menu.clear()
        for trick in sorted(game.resource_database.trick, key=lambda _trick: _trick.long_name):
            if trick not in tricks_in_use or trick.hide_from_ui:
                continue

            trick_menu = QtWidgets.QMenu(self)
            trick_menu.setTitle(_t(trick.long_name))
            menu.addAction(trick_menu.menuAction())

            used_difficulties = trick_lib.difficulties_for_trick(game, trick)
            for trick_level in enum_lib.iterate_enum(LayoutTrickLevel):
                if trick_level in used_difficulties:
                    difficulty_action = QtGui.QAction(self)
                    difficulty_action.setText(trick_level.long_name)
                    trick_menu.addAction(difficulty_action)
                    difficulty_action.triggered.connect(
                        functools.partial(self._open_trick_details_popup, game, trick, trick_level)
                    )

    # Background Update

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

    # ==========

    @asyncSlot()
    async def _on_validate_seed_change(self):
        old_value = self._options.advanced_validate_seed_after
        new_value = self.menu_action_validate_seed_after.isChecked()

        if old_value and not new_value:
            if not await async_dialog.yes_no_prompt(
                self,
                "Disable validation?",
                text=_DISABLE_VALIDATION_WARNING,
                icon=QtWidgets.QMessageBox.Icon.Warning,
            ):
                self.menu_action_validate_seed_after.setChecked(True)
                return

        with self._options as options:
            options.advanced_validate_seed_after = new_value

    def _on_generate_time_limit_change(self):
        is_checked = self.menu_action_timeout_generation_after_a_time_limit.isChecked()
        with self._options as options:
            options.advanced_timeout_during_generation = is_checked

    @asyncSlot()
    async def _on_generate_in_another_process_change(self):
        old_value = self._options.advanced_generate_in_another_process
        new_value = self.menu_action_generate_in_another_process.isChecked()

        if old_value and not new_value:
            if not await async_dialog.yes_no_prompt(
                self,
                "Run generation in the same process?",
                text=_ANOTHER_PROCESS_GENERATION_WARNING,
            ):
                self.menu_action_generate_in_another_process.setChecked(True)
                return

        with self._options as options:
            options.advanced_generate_in_another_process = new_value

    def _on_menu_action_dark_mode(self):
        with self._options as options:
            options.dark_mode = self.menu_action_dark_mode.isChecked()

    def _on_menu_action_show_multiworld_banner(self) -> None:
        banner_val = self.menu_action_show_multiworld_banner.isChecked()
        monitoring.metrics.incr(f"gui_multiworld_banner_option_{"checked" if banner_val else "unchecked"}")
        with self._options as options:
            options.show_multiworld_banner = banner_val

    def _on_menu_action_experimental_settings(self):
        with self._options as options:
            options.experimental_settings = self.menu_action_experimental_settings.isChecked()

    def _open_auto_tracker(self):
        from randovania.gui.auto_tracker_window import AutoTrackerWindow

        self.auto_tracker_window = AutoTrackerWindow(common_qt_lib.get_game_connection(), self, self._options)
        self.auto_tracker_window.show()

    def _on_menu_action_previously_generated_games(self):
        path = self._options.game_history_path
        common_qt_lib.open_directory_in_explorer(
            path,
            common_qt_lib.FallbackDialog(
                "Game History",
                f"Previously generated games can be found at:\n{path}",
                self,
            ),
        )

    def _on_menu_action_log_files_directory(self):
        path = self._options.logs_path
        common_qt_lib.open_directory_in_explorer(
            path,
            common_qt_lib.FallbackDialog(
                "Logs",
                f"Randovania logs can be found at:\n{path}",
                self,
            ),
        )

    def setup_welcome_text(self):
        self.intro_label.setText(self.intro_label.text().format(version=VERSION))

        welcome = get_readme_section("WELCOME")
        supported = get_readme_section("SUPPORTED")
        experimental = get_readme_section("EXPERIMENTAL")

        self.games_supported_label.setText(supported)
        self.games_experimental_label.setText(experimental if randovania.is_dev_version() else "")
        self.intro_welcome_label.setText(welcome)

    def _create_generic_window(self, widget: QtWidgets.QWidget, title: str | None = None) -> QtWidgets.QMainWindow:
        window = QtWidgets.QMainWindow()
        window.setCentralWidget(widget)
        if title is not None:
            window.setWindowTitle(title)
        else:
            window.setWindowTitle(window.windowTitle())
        window.setWindowIcon(self.windowIcon())
        window.resize(self.size())
        return window

    def _on_menu_action_help(self):
        from randovania.gui.widgets.randovania_help_widget import RandovaniaHelpWidget

        if self.help_window is None:
            self.help_window = self._create_generic_window(RandovaniaHelpWidget(), "Randovania Help")
        self.help_window.show()

    @asyncSlot()
    async def _on_menu_action_verify_installation(self):
        try:
            hash_list: dict[str, str] = await json_lib.read_path_async(
                randovania.get_data_path().joinpath("frozen_file_list.json")
            )
        except FileNotFoundError:
            return await async_dialog.warning(
                self, "File List Missing", "Unable to verify installation: file list is missing."
            )

        from randovania.gui.dialog.background_process_dialog import BackgroundProcessDialog

        try:
            bad_files, missing_files, extra_files = await BackgroundProcessDialog.open_for_background_task(
                functools.partial(find_bad_installation, hash_list), "Verifying installation..."
            )
        except asyncio.exceptions.CancelledError:
            return

        if bad_files or extra_files:
            errors = []
            if bad_files:
                errors.append(f"* {len(bad_files)} files are incorrect")

            if missing_files:
                errors.append(f"* {len(missing_files)} files are missing")

            if extra_files:
                errors.append(f"* {len(extra_files)} files are unexpected")

            for m in bad_files:
                logging.warning("Bad file: %s", m)
            for m in missing_files:
                logging.warning("Missing file: %s", m)
            for m in extra_files:
                logging.warning("Unexpected file: %s", m)

            await async_dialog.warning(
                self, "Bad Installation", "The following errors were found:\n" + "\n".join(errors)
            )
        else:
            await async_dialog.message_box(
                self,
                QtWidgets.QMessageBox.Icon.Information,
                "Clean Installation",
                f"No issues found out of {len(hash_list)} files.",
            )

    def _on_menu_action_changelog(self):
        if self.all_change_logs is None:
            return

        if self.changelog_window is None:
            from randovania.gui.widgets.changelog_widget import ChangeLogWidget

            tab = ChangeLogWidget(self.all_change_logs)
            tab.start_fetching_data()
            self.changelog_tab = tab
            self.changelog_window = self._create_generic_window(self.changelog_tab, "Change Log")

        self.changelog_window.show()

    def _on_menu_action_about(self):
        from randovania.gui.widgets.about_widget import AboutWidget

        if self.about_window is None:
            self.about_window = self._create_generic_window(AboutWidget(), "About Randovania")
        self.about_window.show()

    def _on_menu_action_dependencies(self):
        from randovania.gui.widgets.dependencies_widget import DependenciesWidget

        if self.dependencies_window is None:
            self.dependencies_window = self._create_generic_window(DependenciesWidget(), "Dependencies")
        self.dependencies_window.show()

    def _on_menu_action_automatic_reporting(self):
        from randovania.gui.widgets.reporting_optout_widget import ReportingOptOutWidget

        if self.reporting_widget is None:
            self.reporting_widget = ReportingOptOutWidget()

        assert isinstance(self.reporting_widget, ReportingOptOutWidget)
        self.reporting_widget.on_options_changed(self._options)
        self.reporting_widget.show()

    def open_app_navigation_link(self, link: str):
        match = re.match(r"^([^:]+)://(.+)$", link)
        if match is not None:
            kind, param = match.group(1, 2)
            if kind == "help":
                self._on_click_help_link(param)

    def _on_click_help_link(self, tab_name: str):
        self._on_menu_action_help()

        tab = getattr(self.help_window.centralWidget(), tab_name, None)
        if tab is not None:
            self.help_window.centralWidget().setCurrentWidget(tab)

    async def ensure_multiplayer_session_window(
        self, network_client: QtNetworkClient, session_id: int, options: Options
    ):
        session_window = self.opened_session_windows.get(session_id, None)
        if session_window is not None and not session_window.has_closed:
            session_window.activateWindow()
            return

        from randovania.gui.multiplayer_session_window import MultiplayerSessionWindow

        session_window = await MultiplayerSessionWindow.create_and_update(
            network_client,
            session_id,
            self,
            options,
        )
        if session_window is not None:
            self.opened_session_windows[session_id] = session_window
            session_window.show()
