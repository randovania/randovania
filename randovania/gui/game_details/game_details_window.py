import copy
import dataclasses
import typing
from typing import Dict, Optional

from PySide2 import QtCore, QtWidgets, QtGui
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QApplication, QDialog, QAction, QMenu
from qasync import asyncSlot

from randovania.game_description import default_database
from randovania.game_description.game_description import GameDescription
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.game import RandovaniaGame
from randovania.gui import game_specific_gui
from randovania.gui.dialog.scroll_label_dialog import ScrollLabelDialog
from randovania.gui.game_details.game_details_tab import GameDetailsTab
from randovania.gui.game_details.pickup_details_tab import PickupDetailsTab
from randovania.gui.generated.game_details_window_ui import Ui_GameDetailsWindow
from randovania.gui.lib import async_dialog, common_qt_lib, game_exporter
from randovania.gui.lib.background_task_mixin import BackgroundTaskMixin
from randovania.gui.lib.close_event_widget import CloseEventWidget
from randovania.gui.lib.common_qt_lib import set_default_window_icon, prompt_user_for_output_game_log
from randovania.gui.lib.window_manager import WindowManager
from randovania.interface_common import simplified_patcher
from randovania.interface_common.options import Options, InfoAlert
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.layout import preset_describer
from randovania.layout.layout_description import LayoutDescription
from randovania.layout.versioned_preset import VersionedPreset


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
    _window_manager: Optional[WindowManager]
    _player_names: Dict[int, str]
    _pickup_spoiler_current_game: Optional[GameDescription] = None
    _last_percentage: float = 0
    _can_stop_background_process: bool = True
    _game_details_tabs: list[GameDetailsTab]

    def __init__(self, window_manager: Optional[WindowManager], options: Options):
        super().__init__()
        self.setupUi(self)
        set_default_window_icon(self)

        self._options = options
        self._window_manager = window_manager
        self._game_details_tabs = []

        # Ui
        self._tool_button_menu = QMenu(self.tool_button)
        self.tool_button.setMenu(self._tool_button_menu)

        self._action_open_tracker = QAction(self)
        self._action_open_tracker.setText("Open map tracker")
        self._action_open_tracker.setEnabled(self._window_manager is not None)
        self._tool_button_menu.addAction(self._action_open_tracker)

        self._action_copy_permalink = QAction(self)
        self._action_copy_permalink.setText("Copy Permalink")
        self._tool_button_menu.addAction(self._action_copy_permalink)

        self._action_export_preset = QAction(self)
        self._action_export_preset.setText("Export current player's preset")
        self._tool_button_menu.addAction(self._action_export_preset)

        self._action_view_trick_usages = QAction(self)
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
        QApplication.clipboard().setText(self.layout_description.permalink.as_base64_str)

    def _export_log(self):
        all_games = self.layout_description.all_games
        if len(all_games) > 1:
            game_name = "Crossgame Multiworld"
        else:
            game_name = f"{list(all_games)[0].short_name} Randomizer"

        default_name = "{} - {}.{}".format(game_name,
                                           self.layout_description.shareable_word_hash,
                                           self.layout_description.file_extension())
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

    async def _show_dialog_for_prime3_layout(self):
        from randovania.games.prime3.patcher import gollop_corruption_patcher
        from randovania.games.prime3.layout.corruption_cosmetic_patches import CorruptionCosmeticPatches
        from randovania.games.prime3.layout.corruption_configuration import CorruptionConfiguration

        cosmetic = typing.cast(
            CorruptionCosmeticPatches,
            self._options.options_for_game(RandovaniaGame.METROID_PRIME_CORRUPTION).cosmetic_patches,
        )
        configuration = typing.cast(
            CorruptionConfiguration,
            self.layout_description.get_preset(self.current_player_index).configuration,
        )
        patches = self.layout_description.all_patches[self.current_player_index]
        game = default_database.game_description_for(RandovaniaGame.METROID_PRIME_CORRUPTION)

        pickup_names = []
        for index in range(game.world_list.num_pickup_nodes):
            p_index = PickupIndex(index)
            if p_index in patches.pickup_assignment:
                name = patches.pickup_assignment[p_index].pickup.name
            else:
                name = "Missile Expansion"
            pickup_names.append(name)

        layout_string = gollop_corruption_patcher.layout_string_for_items(pickup_names)
        starting_location = patches.starting_location

        suit_type = game.resource_database.get_item_by_name("Suit Type")
        starting_items = copy.copy(patches.starting_items)
        starting_items[suit_type] = starting_items.get(suit_type, 0) + cosmetic.player_suit.value
        if configuration.start_with_corrupted_hypermode:
            hypermode_original = 0
        else:
            hypermode_original = 1

        commands = "\n".join([
            f'set seed="{layout_string}"',
            f'set "starting_items={gollop_corruption_patcher.starting_items_for(starting_items, hypermode_original)}"',
            f'set "starting_location={gollop_corruption_patcher.starting_location_for(game, starting_location)}"',
            f'set "random_door_colors={str(cosmetic.random_door_colors).lower()}"',
            f'set "random_welding_colors={str(cosmetic.random_welding_colors).lower()}"',
        ])
        dialog_text = (
            "There is no integrated patcher for Metroid Prime 3: Corruption games.\n"
            "Download the randomizer for it from #corruption-general in the Metroid Prime Randomizer Discord, "
            "and use the following commands as a seed.\n\n"
            "\n{}").format(commands)

        message_box = ScrollLabelDialog(dialog_text, "Commands for patcher", self)
        message_box.resize(750, 200)
        message_box.label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        QApplication.clipboard().setText(commands)
        await async_dialog.execute_dialog(message_box)

    @property
    def current_player_game(self) -> RandovaniaGame:
        return self.layout_description.get_preset(self.current_player_index).game

    @asyncSlot()
    async def _export_iso(self):
        layout = self.layout_description
        has_spoiler = layout.has_spoiler
        options = self._options

        if not options.is_alert_displayed(InfoAlert.FAQ):
            await async_dialog.message_box(self, QtWidgets.QMessageBox.Icon.Information, "FAQ",
                                           "Have you read the Randovania FAQ?\n"
                                           "It can be found in the main Randovania window → Help → FAQ")
            options.mark_alert_as_displayed(InfoAlert.FAQ)

        game = self.current_player_game
        if game == RandovaniaGame.METROID_PRIME_CORRUPTION:
            return await self._show_dialog_for_prime3_layout()

        cosmetic_patches = options.options_for_game(game).cosmetic_patches
        data_factory = game.patch_data_factory(layout, self.players_configuration, cosmetic_patches)
        patch_data = data_factory.create_data()

        dialog = game.gui.export_dialog(options, patch_data, layout.shareable_word_hash, has_spoiler)
        result = await async_dialog.execute_dialog(dialog)
        if result != QDialog.Accepted:
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

    def update_layout_description(self, description: LayoutDescription):
        self.layout_description = description
        self.layout_info_tab.show()

        self.setWindowTitle(f"Game Details: {description.shareable_word_hash}")
        self.export_log_button.setEnabled(description.has_spoiler)

        self._player_names = {
            i: f"Player {i + 1}"
            for i in range(description.player_count)
        }

        self.export_iso_button.setEnabled(description.player_count == 1)
        if description.player_count > 1:
            self.export_iso_button.setToolTip("Multiworld games can only be exported from a game session")
        else:
            self.export_iso_button.setToolTip("")

        self.customize_user_preferences_button.setVisible(description.player_count == 1)

        self.player_index_combo.clear()
        for i in range(description.player_count):
            self.player_index_combo.addItem(self._player_names[i], i)
        self.player_index_combo.setCurrentIndex(0)
        self.player_index_combo.setVisible(description.player_count > 1)

        if description.has_spoiler:
            action_list_widget = QtWidgets.QListWidget(self.layout_info_tab)
            for item_order in description.item_order:
                action_list_widget.addItem(item_order)
            self.layout_info_tab.addTab(action_list_widget, f"Spoiler: Generation Order")

        self._update_current_player()

    def _update_current_player(self):
        description = self.layout_description
        current_player = self.current_player_index
        preset = description.get_preset(current_player)

        self.permalink_edit.setText(description.permalink.as_base64_str)

        ingame_hash = preset.game.data.layout.get_ingame_hash(description.shareable_hash_bytes)
        ingame_hash_str = f"In-game Hash: {ingame_hash}<br/>" if ingame_hash is not None else ""
        title_text = """
        <p>
            Generated with Randovania {description.randovania_version_text}<br />
            Seed Hash: {description.shareable_word_hash} ({description.shareable_hash})<br/>
            {ingame_hash_str}
            Preset Name: {preset.name}
        </p>
        """.format(description=description, ingame_hash_str=ingame_hash_str, preset=preset)
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
            spoiler_visualizer.insert(0, PickupDetailsTab)
            for missing_tab in spoiler_visualizer:
                new_tab = missing_tab(self.layout_info_tab, preset.game)
                new_tab.update_content(preset.configuration, description.all_patches, players_config)
                self.layout_info_tab.addTab(new_tab.widget(), f"Spoiler: {new_tab.tab_title()}")
                self._game_details_tabs.append(new_tab)

    def _open_user_preferences_dialog(self):
        game = self.current_player_game
        per_game_options = self._options.options_for_game(game)

        dialog = game_specific_gui.create_dialog_for_cosmetic_patches(self, per_game_options.cosmetic_patches)
        result = dialog.exec_()
        if result == QtWidgets.QDialog.Accepted:
            with self._options as options:
                options.set_options_for_game(game, dataclasses.replace(per_game_options,
                                                                       cosmetic_patches=dialog.cosmetic_patches))

    def enable_buttons_with_background_tasks(self, value: bool):
        self.stop_background_process_button.setEnabled(not value and self._can_stop_background_process)
        self.export_iso_button.setEnabled(value)
        simplified_patcher.export_busy = not value

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
