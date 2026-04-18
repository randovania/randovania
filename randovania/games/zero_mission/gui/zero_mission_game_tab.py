from __future__ import annotations

from randovania.game.game_enum import RandovaniaGame
from randovania.games.zero_mission.gui.generated.games_tab_zero_mission_widget_ui import Ui_MZMGameTabWidget
from randovania.gui.widgets.base_game_tab_widget import BaseGameTabWidget


class MZMGameTabWidget(BaseGameTabWidget, Ui_MZMGameTabWidget):
    def setup_ui(self) -> None:
        self.setupUi(self)

    @classmethod
    def game(cls) -> RandovaniaGame:
        return RandovaniaGame.METROID_ZERO_MISSION
