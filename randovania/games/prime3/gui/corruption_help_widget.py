from __future__ import annotations

from randovania.games.game import RandovaniaGame
from randovania.games.prime3.gui.corruption_layout_editor import CorruptionLayoutEditor
from randovania.games.prime3.gui.generated.games_tab_corruption_widget_ui import Ui_CorruptionGameTabWidget
from randovania.gui.widgets.base_game_tab_widget import BaseGameTabWidget


class CorruptionGameTabWidget(BaseGameTabWidget, Ui_CorruptionGameTabWidget):
    def setup_ui(self) -> None:
        self.setupUi(self)
        self.addTab(CorruptionLayoutEditor(), "Layout Editor")

    @classmethod
    def game(cls) -> RandovaniaGame:
        return RandovaniaGame.METROID_PRIME_CORRUPTION
