from __future__ import annotations

from randovania.games.game import RandovaniaGame
from randovania.games.prime2.gui.generated.games_tab_echoes_widget_ui import Ui_EchoesGameTabWidget
from randovania.gui.widgets.base_game_tab_widget import BaseGameTabWidget


class EchoesGameTabWidget(BaseGameTabWidget, Ui_EchoesGameTabWidget):
    def setup_ui(self):
        self.setupUi(self)

    @classmethod
    def game(cls) -> RandovaniaGame:
        return RandovaniaGame.METROID_PRIME_ECHOES
