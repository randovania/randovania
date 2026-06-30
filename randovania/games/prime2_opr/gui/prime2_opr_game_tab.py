from __future__ import annotations

from randovania.game.game_enum import RandovaniaGame
from randovania.games.prime2_opr.gui.generated.games_tab_prime2_opr_widget_ui import Ui_EchoesOPRGameTabWidget
from randovania.gui.widgets.base_game_tab_widget import BaseGameTabWidget


class EchoesOPRGameTabWidget(BaseGameTabWidget, Ui_EchoesOPRGameTabWidget):
    def setup_ui(self) -> None:
        self.setupUi(self)

    @classmethod
    def game(cls) -> RandovaniaGame:
        return RandovaniaGame.METROID_PRIME_ECHOES_OPR
