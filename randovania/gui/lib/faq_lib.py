from PySide2 import QtCore, QtWidgets

from randovania.games.game import RandovaniaGame


def format_game_faq(game: RandovaniaGame, widget: QtWidgets.QLabel):
    widget.setTextFormat(QtCore.Qt.MarkdownText)
    widget.setText("\n\n&nbsp;\n".join(
        "### {}\n{}".format(question, answer)
        for question, answer in game.data.faq
    ))
