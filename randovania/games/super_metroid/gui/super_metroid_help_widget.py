from PySide2 import QtWidgets

from randovania.games.game import RandovaniaGame
from randovania.gui.generated.games_help_prime_widget_ui import Ui_PrimeHelpWidget
from randovania.gui.generated.games_help_supermetroid_widget_ui import Ui_SuperMetroidHelpWidget
from randovania.gui.lib import hints_text, faq_lib


class SuperMetroidHelpWidget(QtWidgets.QTabWidget, Ui_SuperMetroidHelpWidget):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        game = RandovaniaGame.SUPER_METROID
        faq_lib.format_game_faq(game, self.faq_label)
