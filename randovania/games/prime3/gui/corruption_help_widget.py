from randovania.games.game import RandovaniaGame
from randovania.gui.generated.games_tab_corruption_widget_ui import Ui_CorruptionGameTabWidget
from randovania.gui.widgets.base_game_tab_widget import BaseGameTabWidget


class CorruptionGameTabWidget(BaseGameTabWidget, Ui_CorruptionGameTabWidget):
    def setup_ui(self):
        self.setupUi(self)

    @classmethod
    def game(cls) -> RandovaniaGame:
        return RandovaniaGame.METROID_PRIME_CORRUPTION
