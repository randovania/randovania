from PySide2 import QtWidgets

from randovania.games.game import RandovaniaGame
from randovania.gui.generated.games_help_prime_widget_ui import Ui_PrimeHelpWidget
from randovania.gui.lib import hints_text, faq_lib


class PrimeHelpWidget(QtWidgets.QTabWidget, Ui_PrimeHelpWidget):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        game = RandovaniaGame.METROID_PRIME
        faq_lib.format_game_faq(game, self.faq_label)
        hints_text.update_hints_text(game, self.hint_item_names_tree_widget)
