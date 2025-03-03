from __future__ import annotations

import re
from typing import TYPE_CHECKING

from PySide6 import QtCore, QtGui, QtWidgets
from qasync import asyncSlot

from randovania import monitoring
from randovania.game_description import default_database
from randovania.gui.lib import faq_lib, hints_text

if TYPE_CHECKING:
    from randovania.game.game_enum import RandovaniaGame
    from randovania.gui.lib.background_task_mixin import BackgroundTaskMixin
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.gui.widgets.generate_game_widget import GenerateGameWidget
    from randovania.gui.widgets.hint_feature_tab import LocationHintFeatureTab, PickupHintFeatureTab
    from randovania.interface_common.options import Options


class BaseGameTabWidget(QtWidgets.QTabWidget):
    tab_intro: QtWidgets.QWidget
    tab_generate_game: GenerateGameWidget
    quick_generate_button: QtWidgets.QPushButton
    game_cover_label: QtWidgets.QLabel | None = None
    intro_label: QtWidgets.QLabel | None = None
    faq_label: QtWidgets.QLabel | None = None
    pickup_hint_features_tab: PickupHintFeatureTab | None = None
    location_hint_features_tab: LocationHintFeatureTab | None = None
    hint_locations_tree_widget: QtWidgets.QTreeWidget | None = None

    def __init__(self, window_manager: WindowManager, background_task: BackgroundTaskMixin, options: Options):
        super().__init__()
        self.setup_ui()
        self._window_manager = window_manager

        game = self.game()

        background_task.background_tasks_button_lock_signal.connect(self.enable_buttons_with_background_tasks)
        self.quick_generate_button.clicked.connect(self.on_quick_generate)

        return_button = QtWidgets.QPushButton("Back to games")
        return_button.clicked.connect(self._return_to_list)
        self.setCornerWidget(return_button, QtCore.Qt.Corner.TopLeftCorner)

        if self.game_cover_label is not None:
            self.game_cover_label.setPixmap(QtGui.QPixmap(game.data_path.joinpath("assets/cover.png").as_posix()))
            self.game_cover_label.setScaledContents(True)
            self.game_cover_label.setFixedSize(150, 200)

        if self.intro_label is not None:
            self.intro_label.linkActivated.connect(self._on_intro_label_link_clicked)

        if self.faq_label is not None:
            faq_lib.format_game_faq(game, self.faq_label)

        if self.location_hint_features_tab is not None:
            game_description = default_database.game_description_for(game)
            self.location_hint_features_tab.add_features(game_description, self._window_manager)

        if self.pickup_hint_features_tab is not None:
            pickup_db = default_database.pickup_database_for_game(game)
            self.pickup_hint_features_tab.add_features(pickup_db)

        if self.hint_locations_tree_widget is not None:
            hints_text.update_hint_locations(game, self.hint_locations_tree_widget)

        self.tab_generate_game.setup_ui(game, window_manager, background_task, options)
        self._update_quick_generate_text()
        self.tab_generate_game.select_preset_widget.CanGenerate.connect(self._on_can_generate)

    def setup_ui(self) -> None:
        raise NotImplementedError

    @classmethod
    def game(cls) -> RandovaniaGame:
        raise NotImplementedError

    def _on_intro_label_link_clicked(self, link: str) -> None:
        if (info := re.match(r"^tab://(.+)$", link)) is not None:
            target_tab_name = info.group(1)
            for i in range(self.count()):
                if self.tabText(i) == target_tab_name:
                    self.setCurrentIndex(i)
                    return

    def _update_quick_generate_text(self) -> None:
        preset_name = self.tab_generate_game.preset.name
        text = f"Quick Generate ({preset_name})"
        self.quick_generate_button.setText(text)

    def _return_to_list(self) -> None:
        self._window_manager.set_games_selector_visible(True)

    def on_options_changed(self, options: Options) -> None:
        self.tab_generate_game.on_options_changed(options)
        self._update_quick_generate_text()

    @asyncSlot()
    async def on_quick_generate(self) -> None:
        monitoring.metrics.incr("gui_generate_quick", tags={"game": self.game().value})
        await self.tab_generate_game.generate_new_layout(spoiler=True)

    def enable_buttons_with_background_tasks(self, value: bool) -> None:
        self.quick_generate_button.setEnabled(value)

    def _on_can_generate(self, can_generate: bool) -> None:
        self.quick_generate_button.setEnabled(can_generate)

    def select_preset_tab(self) -> None:
        self.setCurrentWidget(self.tab_generate_game)
