from unittest.mock import MagicMock

import pytest
from PySide6 import QtGui

from randovania.games.game import RandovaniaGame
from randovania.gui.widgets.games_help_widget import GamesHelpWidget


def test_on_first_show_after_set_experimental(skip_qtbot, is_dev_version):
    # Setup

    widget = GamesHelpWidget()
    widget.set_experimental_visible(True)

    # Run
    widget._on_first_show()

    # Assert
    visibility = {
        game: widget.isTabVisible(index)
        for game, index in widget._index_for_game.items()
    }
    assert visibility == {
        game: game.data.development_state.can_view(True)
        for game in RandovaniaGame.all_games()
        if game.gui.help_widget is not None
    }


def test_set_experimental_visible_before_show(skip_qtbot, is_dev_version):
    # Setup
    widget = GamesHelpWidget()

    # Run
    widget.set_experimental_visible(False)

    # Assert
    assert widget.currentWidget() is None


def test_set_experimental_visible_after_show(skip_qtbot, is_dev_version):
    # Setup
    widget = GamesHelpWidget()
    widget._on_first_show()

    assert widget._index_for_game
    for game, index in widget._index_for_game.items():
        assert widget.isTabVisible(index) != game.data.development_state

    # Run
    widget.set_experimental_visible(True)

    # Assert
    visibility = {
        game: widget.isTabVisible(index)
        for game, index in widget._index_for_game.items()
    }
    assert visibility == {
        game: game.data.development_state.can_view(True)
        for game in RandovaniaGame.all_games()
        if game.gui.help_widget is not None
    }


def test_showEvent_twice(skip_qtbot):
    # Setup
    widget = GamesHelpWidget()
    widget._on_first_show = MagicMock()

    # Run
    widget.showEvent(QtGui.QShowEvent())
    widget.showEvent(QtGui.QShowEvent())

    # Assert
    widget._on_first_show.assert_called_once_with()
