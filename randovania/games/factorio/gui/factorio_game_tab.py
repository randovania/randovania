from __future__ import annotations

from randovania.games.factorio.gui.generated.games_tab_factorio_widget_ui import Ui_FactorioGameTabWidget
from randovania.games.game import RandovaniaGame
from randovania.gui.widgets.base_game_tab_widget import BaseGameTabWidget


class FactorioGameTabWidget(BaseGameTabWidget, Ui_FactorioGameTabWidget):
    def setup_ui(self) -> None:
        self.setupUi(self)

    @classmethod
    def game(cls) -> RandovaniaGame:
        return RandovaniaGame.FACTORIO
