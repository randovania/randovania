from randovania.games.game import RandovaniaGame
from randovania.gui.generated.games_tab_prime_widget_ui import Ui_PrimeGameTabWidget
from randovania.gui.widgets.base_game_tab_widget import BaseGameTabWidget


class PrimeGameTabWidget(BaseGameTabWidget, Ui_PrimeGameTabWidget):
    def setup_ui(self):
        self.setupUi(self)

    @classmethod
    def game(cls) -> RandovaniaGame:
        return RandovaniaGame.METROID_PRIME
