from randovania.games.game import RandovaniaGame
from randovania.gui.generated.games_tab_samusreturns_widget_ui import Ui_SamusReturnsGameTabWidget
from randovania.gui.widgets.base_game_tab_widget import BaseGameTabWidget


class MSRGameTabWidget(BaseGameTabWidget, Ui_SamusReturnsGameTabWidget):
    def setup_ui(self):
        self.setupUi(self)

    @classmethod
    def game(cls) -> RandovaniaGame:
        return RandovaniaGame.METROID_SAMUS_RETURNS
