from typing import Optional

from PySide2 import QtWidgets, QtGui

from randovania.games.game import RandovaniaGame


class GamesHelpWidget(QtWidgets.QTabWidget):
    _first_show: bool = True
    _experimental_visible: bool = False
    _index_for_game: Optional[dict[RandovaniaGame, int]] = None

    def _on_first_show(self):
        self._index_for_game = {}

        for game in RandovaniaGame.sorted_all_games():
            if game.gui.help_widget is None:
                continue

            index = self.addTab(game.gui.help_widget(), game.long_name)
            self.setTabVisible(index, game.data.development_state.can_view(self._experimental_visible))
            self._index_for_game[game] = index

    def showEvent(self, arg: QtGui.QShowEvent) -> None:
        if self._first_show:
            self._first_show = False
            self._on_first_show()

        return super().showEvent(arg)

    def set_experimental_visible(self, visible: bool):
        self._experimental_visible = visible
        if self._index_for_game is not None:
            for game, index in self._index_for_game.items():
                self.setTabVisible(index, game.data.development_state.can_view(self._experimental_visible))
