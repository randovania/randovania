from __future__ import annotations

from unittest.mock import MagicMock

from PySide6 import QtGui

from randovania.games.game import RandovaniaGame
from randovania.gui.widgets.games_help_widget import GamesHelpWidget


def test_on_first_show_tab_visibility(skip_qtbot, is_dev_version):
    # Setup

    widget = GamesHelpWidget()
    widget._last_options = MagicMock()
    widget.set_main_window(MagicMock())

    # Run
    widget._on_first_show()

    # Assert
    visibility = {game: widget.isTabVisible(index) for game, index in widget._index_for_game.items()}
    assert visibility == {game: game.data.development_state.can_view() for game in RandovaniaGame.all_games()}


def test_showEvent_twice(skip_qtbot):
    # Setup
    widget = GamesHelpWidget()
    widget._on_first_show = MagicMock()

    # Run
    widget.showEvent(QtGui.QShowEvent())
    widget.showEvent(QtGui.QShowEvent())

    # Assert
    widget._on_first_show.assert_called_once_with()


def test_game_tab_created(skip_qtbot):
    # Setup
    game = RandovaniaGame.METROID_PRIME_ECHOES
    widget = GamesHelpWidget()
    widget.set_main_window(MagicMock())
    widget.on_options_changed(MagicMock())

    skip_qtbot.addWidget(widget)
    widget.set_current_game(game)

    # Run
    widget.showEvent(None)
    assert widget.current_game() is game
    assert isinstance(widget.current_game_widget(), game.gui.game_tab)
