from PySide6 import QtWidgets

from randovania.games.game import RandovaniaGame
from randovania.gui.generated.games_help_corruption_widget_ui import Ui_CorruptionHelpWidget
from randovania.gui.generated.games_help_prime_widget_ui import Ui_PrimeHelpWidget
from randovania.gui.lib import hints_text, faq_lib


class CorruptionHelpWidget(QtWidgets.QTabWidget, Ui_CorruptionHelpWidget):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        game = RandovaniaGame.METROID_PRIME_CORRUPTION
        hints_text.update_hints_text(game, self.hint_item_names_tree_widget)
