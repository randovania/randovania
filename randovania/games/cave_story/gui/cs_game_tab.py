from __future__ import annotations

from randovania.games.cave_story.gui.generated.games_tab_cavestory_widget_ui import Ui_CaveStoryGameTabWidget
from randovania.games.game import RandovaniaGame
from randovania.gui.widgets.base_game_tab_widget import BaseGameTabWidget


class CSGameTabWidget(BaseGameTabWidget, Ui_CaveStoryGameTabWidget):
    def setup_ui(self):
        self.setupUi(self)

    @classmethod
    def game(cls) -> RandovaniaGame:
        return RandovaniaGame.CAVE_STORY
