from __future__ import annotations

from randovania.game.game_enum import RandovaniaGame
from randovania.games.prime_origins.gui.generated.games_tab_prime_origins_widget_ui import Ui_MPOGameTabWidget
from randovania.gui.widgets.base_game_tab_widget import BaseGameTabWidget


class MPOGameTabWidget(BaseGameTabWidget, Ui_MPOGameTabWidget):
    def setup_ui(self) -> None:
        self.setupUi(self)

    @classmethod
    def game(cls) -> RandovaniaGame:
        return RandovaniaGame.PRIME_ORIGINS
