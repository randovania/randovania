from __future__ import annotations

from randovania.games.game import RandovaniaGame
from randovania.games.planets_zebeth.gui.generated.games_tab_planets_zebeth_widget_ui import (
    Ui_PlanetsZebethGameTabWidget,
)
from randovania.gui.widgets.base_game_tab_widget import BaseGameTabWidget


class PlanetsZebethGameTabWidget(BaseGameTabWidget, Ui_PlanetsZebethGameTabWidget):
    def setup_ui(self) -> None:
        self.setupUi(self)

    @classmethod
    def game(cls) -> RandovaniaGame:
        return RandovaniaGame.METROID_PLANETS_ZEBETH
