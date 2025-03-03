from __future__ import annotations

from randovania.game.game_enum import RandovaniaGame
from randovania.games.dread.gui.generated.games_tab_dread_widget_ui import Ui_DreadGameTabWidget
from randovania.gui.widgets.base_game_tab_widget import BaseGameTabWidget


class DreadGameTabWidget(BaseGameTabWidget, Ui_DreadGameTabWidget):
    def setup_ui(self) -> None:
        self.setupUi(self)

    @classmethod
    def game(cls) -> RandovaniaGame:
        return RandovaniaGame.METROID_DREAD
