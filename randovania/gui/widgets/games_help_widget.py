from PySide6 import QtWidgets, QtGui

from randovania.games.game import RandovaniaGame


class GamesHelpWidget(QtWidgets.QTabWidget):
    _first_show: bool = True
    _experimental_visible: bool = False
    _index_for_game: dict[RandovaniaGame, int] | None = None
    _layout_for_index: dict[int, QtWidgets.QVBoxLayout] | None = None
    _games_with_widget: set[RandovaniaGame] | None = None

    def _on_first_show(self):
        self._index_for_game = {}
        self._layout_for_index = {}
        self._games_with_widget = set()

        for game in RandovaniaGame.sorted_all_games():
            if game.gui.help_widget is None:
                continue

            widget = QtWidgets.QWidget()
            widget.game = game
            widget_layout = QtWidgets.QVBoxLayout(widget)
            widget_layout.setContentsMargins(0, 0, 0, 0)

            index = self.addTab(widget, game.long_name)
            self.setTabVisible(index, game.data.development_state.can_view(self._experimental_visible))
            self._index_for_game[game] = index
            self._layout_for_index[index] = widget_layout

        self.currentChanged.connect(self.ensure_current_game_has_widget)
        self.ensure_current_game_has_widget()

    def current_game(self) -> RandovaniaGame | None:
        for game, index in self._index_for_game.items():
            if index == self.currentIndex():
                return game
        return None

    def ensure_current_game_has_widget(self):
        game = self.current_game()
        if game is not None and game not in self._games_with_widget:
            self._games_with_widget.add(game)
            self._layout_for_index[self.currentIndex()].addWidget(
                game.gui.help_widget(),
            )

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
