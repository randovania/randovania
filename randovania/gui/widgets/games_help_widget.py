from __future__ import annotations

import logging
import os
import typing

from PySide6 import QtWidgets, QtGui, QtCore

from randovania.games.game import RandovaniaGame
from randovania.gui.widgets.base_game_tab_widget import BaseGameTabWidget
from randovania.interface_common.options import Options

if typing.TYPE_CHECKING:
    from randovania.gui.main_window import MainWindow


class GamesHelpWidget(QtWidgets.QTabWidget):
    _main_window: MainWindow
    _last_options: Options
    _first_show: bool = True
    _experimental_visible: bool = False
    _index_for_game: dict[RandovaniaGame, int] | None = None
    _layout_for_index: dict[int, QtWidgets.QVBoxLayout] | None = None
    _widget_for_game: dict[RandovaniaGame, BaseGameTabWidget] | None = None
    _pending_current_game: RandovaniaGame | None = None

    def _on_first_show(self):
        self._index_for_game = {}
        self._layout_for_index = {}
        self._widget_for_game = {}

        self.tabBar().setVisible(False)

        for game in RandovaniaGame.sorted_all_games():
            widget = QtWidgets.QWidget()
            widget.game = game
            widget_layout = QtWidgets.QVBoxLayout(widget)
            widget_layout.setContentsMargins(0, 0, 0, 0)

            index = self.addTab(widget, game.long_name)
            self.setTabVisible(index, game.data.development_state.can_view())
            self._index_for_game[game] = index
            self._layout_for_index[index] = widget_layout

        if self._pending_current_game is not None:
            self.set_current_game(self._pending_current_game)
            self._pending_current_game = None

        self.currentChanged.connect(self.ensure_current_game_has_widget)
        self.ensure_current_game_has_widget()

    def set_main_window(self, window):
        self._main_window = window

    def current_game(self) -> RandovaniaGame | None:
        if self._index_for_game is not None:
            for game, index in self._index_for_game.items():
                if index == self.currentIndex():
                    return game
        return None

    def current_game_widget(self) -> BaseGameTabWidget | None:
        if self._widget_for_game is not None:
            return self._widget_for_game.get(self.current_game())
        return None

    def ensure_current_game_has_widget(self):
        game = self.current_game()
        if game is not None and game not in self._widget_for_game:
            new_tab = game.gui.game_tab(self._main_window, self._main_window, self._last_options)
            self._widget_for_game[game] = new_tab
            self._layout_for_index[self.currentIndex()].addWidget(new_tab)
            new_tab.on_options_changed(self._last_options)

    def showEvent(self, arg: QtGui.QShowEvent) -> None:
        if self._first_show:
            self._first_show = False
            self._on_first_show()

        return super().showEvent(arg)

    def set_current_game(self, game: RandovaniaGame):
        if self._first_show:
            self._pending_current_game = game
        else:
            self.setCurrentIndex(self._index_for_game[game])

    def on_options_changed(self, options: Options):
        self._last_options = options
        if self._widget_for_game is not None:
            for widget in self._widget_for_game.values():
                widget.on_options_changed(options)
