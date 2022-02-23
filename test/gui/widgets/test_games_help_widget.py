from unittest.mock import MagicMock

from PySide2 import QtGui

from randovania.gui.widgets.games_help_widget import GamesHelpWidget


def test_on_first_show_after_set_experimental(skip_qtbot):
    # Setup
    widget = GamesHelpWidget()
    widget.set_experimental_visible(True)

    # Run
    widget._on_first_show()

    # Assert
    for game, index in widget._index_for_game.items():
        assert widget.isTabVisible(index)


def test_set_experimental_visible_before_show(skip_qtbot):
    # Setup
    widget = GamesHelpWidget()

    # Run
    widget.set_experimental_visible(False)

    # Assert
    assert widget.currentWidget() is None


def test_set_experimental_visible_after_show(skip_qtbot):
    # Setup
    widget = GamesHelpWidget()
    widget._on_first_show()

    assert widget._index_for_game
    for game, index in widget._index_for_game.items():
        assert widget.isTabVisible(index) != game.data.development_state

    # Run
    widget.set_experimental_visible(True)

    # Assert
    for game, index in widget._index_for_game.items():
        assert widget.isTabVisible(index)


def test_showEvent_twice(skip_qtbot):
    # Setup
    widget = GamesHelpWidget()
    widget._on_first_show = MagicMock()

    # Run
    widget.showEvent(QtGui.QShowEvent())
    widget.showEvent(QtGui.QShowEvent())

    # Assert
    widget._on_first_show.assert_called_once_with()
