from PySide6 import QtWidgets

from randovania.games.game import RandovaniaGame
from randovania.gui.generated.games_help_dread_widget_ui import Ui_DreadHelpWidget
from randovania.gui.lib import hints_text, faq_lib


class DreadHelpWidget(QtWidgets.QTabWidget, Ui_DreadHelpWidget):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        game = RandovaniaGame.METROID_DREAD
        faq_lib.format_game_faq(game, self.faq_label)
        hints_text.update_hints_text(game, self.hint_item_names_tree_widget)
        hints_text.update_hint_locations(game, self.hint_locations_tree_widget)
