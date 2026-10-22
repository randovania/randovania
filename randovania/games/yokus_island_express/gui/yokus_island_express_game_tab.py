from __future__ import annotations

from randovania.game.game_enum import RandovaniaGame
from randovania.games.yokus_island_express.gui.generated.games_tab_yokus_island_express_widget_ui import (
    Ui_YokuGameTabWidget,
)
from randovania.gui.widgets.base_game_tab_widget import BaseGameTabWidget


class YokuGameTabWidget(BaseGameTabWidget, Ui_YokuGameTabWidget):
    def setup_ui(self) -> None:
        self.setupUi(self)

    @classmethod
    def game(cls) -> RandovaniaGame:
        return RandovaniaGame.YOKUS_ISLAND_EXPRESS
