from __future__ import annotations

import dataclasses
import typing

from PySide6 import QtCore, QtGui, QtWidgets
from qasync import asyncSlot

import randovania
from randovania import monitoring
from randovania.gui import game_specific_gui
from randovania.gui.game_details.dock_lock_details_tab import DockLockDetailsTab
from randovania.gui.game_details.generation_order_widget import GenerationOrderWidget
from randovania.gui.game_details.pickup_details_tab import PickupDetailsTab
from randovania.gui.generated.game_details_window_ui import Ui_GameDetailsWindow
from randovania.gui.lib import async_dialog, common_qt_lib, game_exporter
from randovania.gui.lib.background_task_mixin import BackgroundTaskMixin
from randovania.gui.lib.close_event_widget import CloseEventWidget
from randovania.gui.lib.common_qt_lib import (
    prompt_user_for_output_game_log,
    set_default_window_icon,
)
from randovania.gui.widgets.game_validator_widget import GameValidatorWidget
from randovania.interface_common import generator_frontend
from randovania.interface_common.options import InfoAlert, Options
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.layout import preset_describer
from randovania.layout.versioned_preset import VersionedPreset

if typing.TYPE_CHECKING:
    from randovania.games.game import RandovaniaGame
    from randovania.gui.game_details.game_details_tab import GameDetailsTab
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.layout.layout_description import LayoutDescription


def _unique(iterable):
    seen = set()

    for item in iterable:
        if item in seen:
            continue
        seen.add(item)
        yield item


class GameDetailsWindow(CloseEventWidget, Ui_GameDetailsWindow, BackgroundTaskMixin):
    _on_bulk_change: bool = False
    layout_description: LayoutDescription
    _options: Options
    _window_manager: WindowManager | None
    _player_names: dict[int, str]
    _last_percentage: float = 0
    _can_stop_background_process: bool = True
    _game_details_tabs: list[GameDetailsTab]
    validator_widget: GameValidatorWidget | None = None

    def __init__(self, window_manager: WindowManager | None, options: Options):
        super().__init__()
        self.setupUi(self)
        set_default_window_icon(self)

        self._options = options
        self._window_manager = window_manager
        self._game_details_tabs = []

        # Ui
        self._tool_button_menu = QtWidgets.QMenu(self.tool_button)
        self.tool_button.setMenu(self._tool_button_menu)
        self.tool_button.triggered.connect(lambda: monitoring.metrics.incr("gui_export_window_tool_button_clicked"))

        self._action_open_tracker = QtGui.QAction(self)
        self._action_open_tracker.setText("Open map tracker")
        self._action_open_tracker.setEnabled(self._window_manager is not None)
        self._tool_button_menu.addAction(self._action_open_tracker)

        self._action_copy_permalink = QtGui.QAction(self)
        self._action_copy_permalink.setText("Copy Permalink")
        self._tool_button_menu.addAction(self._action_copy_permalink)

        self._action_export_preset = QtGui.QAction(self)
        self._action_export_preset.setText("Export current player's preset")
        self._tool_button_menu.addAction(self._action_export_preset)

        self._action_view_trick_usages = QtGui.QAction(self)
        self._action_view_trick_usages.setText("View current player's expected trick usage")
        self._tool_button_menu.addAction(self._action_view_trick_usages)

        # Signals
        self.export_log_button.clicked.connect(self._export_log)
        self.export_iso_button.clicked.connect(self._export_iso)
        self._action_open_tracker.triggered.connect(self._open_map_tracker)
        self._action_copy_permalink.triggered.connect(self._copy_permalink)
        self._action_export_preset.triggered.connect(self._export_preset)
        self._action_view_trick_usages.triggered.connect(self._view_trick_usages)
        self.player_index_combo.activated.connect(self._update_current_player)
        self.CloseEvent.connect(self.stop_background_process)

        # Progress
        self.background_tasks_button_lock_signal.connect(self.enable_buttons_with_background_tasks)
        self.progress_update_signal.connect(self.update_progress)
        self.stop_background_process_button.clicked.connect(self.stop_background_process)

        # Cosmetic
        self.customize_user_preferences_button.clicked.connect(self._open_user_preferences_dialog)

    def closeEvent(self, event: QtGui.QCloseEvent):
        if self.validator_widget is not None:
            self.validator_widget.stop_validator()

        return super().closeEvent(event)

    @property
    def current_player_index(self) -> int:
        return self.player_index_combo.currentData()

    @property
    def players_configuration(self) -> PlayersConfiguration:
        return PlayersConfiguration(
            player_index=self.current_player_index,
            player_names=self._player_names,
        )

    # Operations
    def _copy_permalink(self):
        common_qt_lib.set_clipboard(self.layout_description.permalink.as_base64_str)

    def _export_log(self):
        all_games = self.layout_description.all_games
        if len(all_games) > 1:
            game_name = "Crossgame Multiworld"
        else:
            game_name = f"{list(all_games)[0].short_name} Randomizer"

        default_name = (
            f"{game_name} - {self.layout_description.shareable_word_hash}.{self.layout_description.file_extension()}"
        )
        json_path = prompt_user_for_output_game_log(self, default_name=default_name)
        if json_path is not None:
            self.layout_description.save_to_file(json_path)

    def _export_preset(self):
        preset = self.layout_description.get_preset(self.current_player_index)
        output_path = common_qt_lib.prompt_user_for_preset_file(self, new_file=True)
        if output_path is not None:
            VersionedPreset.with_preset(preset).save_to_file(output_path)

    def _view_trick_usages(self):
        from randovania.gui.dialog.trick_usage_popup import TrickUsagePopup

        preset = self.layout_description.get_preset(self.current_player_index)
        self._trick_usage_popup = TrickUsagePopup(self, self._window_manager, preset)
        self._trick_usage_popup.setWindowModality(QtCore.Qt.WindowModal)
        self._trick_usage_popup.open()

    @property
    def current_player_game(self) -> RandovaniaGame:
        return self.layout_description.get_preset(self.current_player_index).game

    @asyncSlot()
    async def _export_iso(self):
        layout = self.layout_description
        has_spoiler = layout.has_spoiler
        options = self._options

        game = self.current_player_game

        if not options.is_alert_displayed(InfoAlert.FAQ):
            monitoring.metrics.incr("gui_export_window_alert_shown", tags={"game": game.short_name})
            await async_dialog.message_box(
                self,
                QtWidgets.QMessageBox.Icon.Information,
                "FAQ",
                "Have you read the Randovania FAQ?\nIt can be found in the main Randovania window → Help → FAQ",
            )
            options.mark_alert_as_displayed(InfoAlert.FAQ)

        monitoring.metrics.incr("gui_export_window_export_clicked", tags={"game": game.short_name})

        cosmetic_patches = options.options_for_game(game).cosmetic_patches
        data_factory = game.patch_data_factory(layout, self.players_configuration, cosmetic_patches)
        patch_data = data_factory.create_data()

        dialog = game.gui.export_dialog(
            options,
            patch_data,
            layout.shareable_word_hash,
            has_spoiler,
            list(layout.all_games),
        )
        result = await async_dialog.execute_dialog(dialog)
        if result != QtWidgets.QDialog.DialogCode.Accepted:
            return

        dialog.save_options()
        self._can_stop_background_process = game.exporter.export_can_be_aborted
        await game_exporter.export_game(
            exporter=game.exporter,
            export_dialog=dialog,
            patch_data=patch_data,
            layout_for_spoiler=layout,
            background=self,
            progress_update_signal=self.progress_update_signal,
        )
        self._can_stop_background_process = True

    @asyncSlot()
    async def _open_map_tracker(self):
        current_preset = self.layout_description.get_preset(self.current_player_index)
        await self._window_manager.open_map_tracker(current_preset)

    # Layout Visualization

    def update_layout_description(self, description: LayoutDescription, players: list[str] | None = None):
        self.layout_description = description
        self.layout_info_tab.show()

        self.setWindowTitle(f"Game Details: {description.shareable_word_hash}")
        self.export_log_button.setText("Save Spoiler" if description.has_spoiler else "Save to file")

        numbered_players = [f"Player {i + 1}" for i in range(description.world_count)]
        if players is None:
            players = numbered_players
        self._player_names = dict(enumerate(players))
        assert len(self._player_names) == len(players)

        self.export_iso_button.setEnabled(description.world_count == 1 or not randovania.is_frozen())
        if description.world_count > 1:
            self.export_iso_button.setToolTip("Multiworld games can only be exported from a game session")
        else:
            self.export_iso_button.setToolTip("")

        has_user_preferences = False
        if description.world_count == 1:
            has_user_preferences = description.get_preset(0).game.gui.cosmetic_dialog is not None
        self.customize_user_preferences_button.setVisible(has_user_preferences)

        self.player_index_combo.clear()
        for i in range(description.world_count):
            self.player_index_combo.addItem(self._player_names[i], i)
        self.player_index_combo.setCurrentIndex(0)
        self.player_index_combo.setVisible(description.world_count > 1)

        if description.has_spoiler:
            exists_minimal_logic = any(
                preset.configuration.trick_level.minimal_logic for preset in description.all_presets
            )
            if description.world_count == 1 and not exists_minimal_logic:
                if self.validator_widget is not None:
                    self.validator_widget.stop_validator()

                self.validator_widget = GameValidatorWidget(self.layout_description)
                self.layout_info_tab.addTab(self.validator_widget, "Spoiler: Playthrough")

            if not any(preset.configuration.should_hide_generation_log() for preset in description.all_presets):
                self.layout_info_tab.addTab(
                    GenerationOrderWidget(None, description, players),
                    "Spoiler: Generation Order",
                )

        self._update_current_player()

    def _update_current_player(self):
        description = self.layout_description
        current_player = self.current_player_index
        preset = description.get_preset(current_player)

        self.permalink_edit.setText(description.permalink.as_base64_str)

        ingame_hash = preset.game.data.layout.get_ingame_hash(description.shareable_hash_bytes)
        ingame_hash_str = f"In-game Hash: {ingame_hash}<br/>" if ingame_hash is not None else ""
        title_text = f"""
        <p>
            Generated with Randovania {description.randovania_version_text}<br />
            Seed Hash: {description.shareable_word_hash} ({description.shareable_hash})<br/>
            {ingame_hash_str}
            Preset Name: {preset.name}
        </p>
        """
        self.layout_title_label.setText(title_text)

        categories = list(preset_describer.describe(preset))
        self.layout_description_left_label.setText(preset_describer.merge_categories(categories[::2]))
        self.layout_description_right_label.setText(preset_describer.merge_categories(categories[1::2]))

        # Game Spoiler
        for tab in self._game_details_tabs:
            self.layout_info_tab.removeTab(self.layout_info_tab.indexOf(tab.widget()))
        self._game_details_tabs.clear()

        if description.has_spoiler:
            players_config = self.players_configuration

            spoiler_visualizer = list(preset.game.gui.spoiler_visualizer)
            spoiler_visualizer.insert(0, DockLockDetailsTab)
            spoiler_visualizer.insert(0, PickupDetailsTab)
            for missing_tab in spoiler_visualizer:
                if not missing_tab.should_appear_for(preset.configuration, description.all_patches, players_config):
                    continue
                new_tab = missing_tab(self.layout_info_tab, preset.game)
                new_tab.update_content(preset.configuration, description.all_patches, players_config)
                self.layout_info_tab.addTab(new_tab.widget(), f"Spoiler: {new_tab.tab_title()}")
                self._game_details_tabs.append(new_tab)

    def _open_user_preferences_dialog(self):
        game = self.current_player_game
        monitoring.metrics.incr("gui_export_window_cosmetic_clicked", tags={"game": game.short_name})
        per_game_options = self._options.options_for_game(game)

        dialog = game_specific_gui.create_dialog_for_cosmetic_patches(self, per_game_options.cosmetic_patches)
        result = dialog.exec_()
        if result == QtWidgets.QDialog.DialogCode.Accepted:
            with self._options as options:
                options.set_options_for_game(
                    game,
                    dataclasses.replace(per_game_options, cosmetic_patches=dialog.cosmetic_patches),
                )

    def enable_buttons_with_background_tasks(self, value: bool):
        self.stop_background_process_button.setEnabled(not value and self._can_stop_background_process)
        self.export_iso_button.setEnabled(value)
        generator_frontend.export_busy = not value

    def update_progress(self, message: str, percentage: int):
        self.progress_label.setText(message)
        if "Aborted" in message:
            percentage = 0

        if percentage is None:
            percentage = self._last_percentage
        else:
            self._last_percentage = percentage
        if percentage >= 0:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(percentage)
        else:
            self.progress_bar.setRange(0, 0)

    def ignore_close_event(self, event: QtGui.QCloseEvent) -> bool:
        return not self._can_stop_background_process
