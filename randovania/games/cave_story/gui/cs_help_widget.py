from PySide6 import QtWidgets

from randovania.games.game import RandovaniaGame
from randovania.gui.generated.games_help_cavestory_widget_ui import Ui_CaveStoryHelpWidget
from randovania.gui.lib import hints_text


class CSHelpWidget(QtWidgets.QTabWidget, Ui_CaveStoryHelpWidget):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        game = RandovaniaGame.CAVE_STORY
        hints_text.update_hints_text(game, self.hint_item_names_tree_widget)
        hints_text.update_hint_locations(game, self.hint_locations_tree_widget)
