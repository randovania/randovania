from randovania.games.game import RandovaniaGame
from randovania.gui.generated.games_tab_blank_widget_ui import Ui_BlankGameTabWidget
from randovania.gui.widgets.base_game_tab_widget import BaseGameTabWidget


class BlankGameTabWidget(BaseGameTabWidget, Ui_BlankGameTabWidget):
    def setup_ui(self):
        self.setupUi(self)

    @classmethod
    def game(cls) -> RandovaniaGame:
        return RandovaniaGame.BLANK
