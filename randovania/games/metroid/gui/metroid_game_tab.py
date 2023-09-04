from __future__ import annotations

from randovania.games.game import RandovaniaGame
from randovania.gui.generated.games_tab_metroid_widget_ui import Ui_MetroidGameTabWidget
from randovania.gui.widgets.base_game_tab_widget import BaseGameTabWidget


class MetroidGameTabWidget(BaseGameTabWidget, Ui_MetroidGameTabWidget):
    def setup_ui(self):
        self.setupUi(self)

    @classmethod
    def game(cls) -> RandovaniaGame:
        return RandovaniaGame.METROID
