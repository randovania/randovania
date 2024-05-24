from __future__ import annotations

from randovania.games.fusion.gui.generated.games_tab_fusion_widget_ui import Ui_FusionGameTabWidget
from randovania.games.game import RandovaniaGame
from randovania.gui.widgets.base_game_tab_widget import BaseGameTabWidget


class FusionGameTabWidget(BaseGameTabWidget, Ui_FusionGameTabWidget):
    def setup_ui(self) -> None:
        self.setupUi(self)

    @classmethod
    def game(cls) -> RandovaniaGame:
        return RandovaniaGame.FUSION
