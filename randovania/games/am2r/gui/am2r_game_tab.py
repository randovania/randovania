from __future__ import annotations

from randovania.game.game_enum import RandovaniaGame
from randovania.games.am2r.gui.generated.games_tab_am2r_widget_ui import Ui_AM2RGameTabWidget
from randovania.gui.widgets.base_game_tab_widget import BaseGameTabWidget


class AM2RGameTabWidget(BaseGameTabWidget, Ui_AM2RGameTabWidget):
    def setup_ui(self):
        self.setupUi(self)

    @classmethod
    def game(cls) -> RandovaniaGame:
        return RandovaniaGame.AM2R
