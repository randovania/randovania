from typing import Optional

from PySide2 import QtWidgets, QtGui


class DelayedTextLabel(QtWidgets.QLabel):
    _already_shown: bool = False
    _delayed_text: Optional[str] = None

    def showEvent(self, event: QtGui.QShowEvent) -> None:
        self._already_shown = True
        if self._delayed_text is not None:
            self.setText(self._delayed_text)
        return super().showEvent(event)

    def setText(self, t: str) -> None:
        if self._already_shown:
            self._delayed_text = None
            return super().setText(t)
        else:
            self._delayed_text = t

    def text(self) -> str:
        if self._already_shown:
            return super().text()
        else:
            return self._delayed_text
