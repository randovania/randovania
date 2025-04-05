from __future__ import annotations

from randovania.game.game_enum import RandovaniaGame
from randovania.games.prime_hunters.gui.generated.games_tab_prime_hunters_widget_ui import Ui_HuntersGameTabWidget
from randovania.gui.widgets.base_game_tab_widget import BaseGameTabWidget


class HuntersGameTabWidget(BaseGameTabWidget, Ui_HuntersGameTabWidget):
    def setup_ui(self) -> None:
        self.setupUi(self)

    @classmethod
    def game(cls) -> RandovaniaGame:
        return RandovaniaGame.METROID_PRIME_HUNTERS
