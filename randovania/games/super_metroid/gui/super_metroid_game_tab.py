from __future__ import annotations

from randovania.games.game import RandovaniaGame
from randovania.games.super_metroid.gui.generated.games_tab_supermetroid_widget_ui import Ui_SuperMetroidGameTabWidget
from randovania.gui.widgets.base_game_tab_widget import BaseGameTabWidget


class SuperMetroidGameTabWidget(BaseGameTabWidget, Ui_SuperMetroidGameTabWidget):
    def setup_ui(self):
        self.setupUi(self)

    @classmethod
    def game(cls) -> RandovaniaGame:
        return RandovaniaGame.SUPER_METROID
