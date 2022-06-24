from PySide6 import QtCore, QtWidgets

from randovania.games.game import RandovaniaGame


def format_game_faq(game: RandovaniaGame, widget: QtWidgets.QLabel):
    widget.setTextFormat(QtCore.Qt.MarkdownText)
    widget.setText("\n\n&nbsp;\n".join(
        f"### {question}\n{answer}"
        for question, answer in game.data.faq
    ))
