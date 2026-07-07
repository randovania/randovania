from __future__ import annotations

import typing

from PySide6 import QtCore, QtWidgets


class ScrollMessageBox(QtWidgets.QMessageBox):
    def __init__(
        self,
        icon: QtWidgets.QMessageBox.Icon,
        title: str,
        text: str,
        /,
        buttons: QtWidgets.QMessageBox.StandardButton = QtWidgets.QMessageBox.StandardButton.Ok,
        parent: QtWidgets.QWidget | None = None,
        flags: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Dialog | QtCore.Qt.WindowType.MSWindowsFixedSizeDialogHint,
        *,
        default_button: QtWidgets.QMessageBox.StandardButton | None = QtWidgets.QMessageBox.StandardButton.Ok,
    ):
        super().__init__(icon, title, text, buttons, parent, flags)

        children = self.children()

        grid = self.findChild(QtWidgets.QGridLayout)
        assert isinstance(grid, QtWidgets.QGridLayout)

        old_label: QtWidgets.QLabel | None = None
        position: tuple[int, int, int, int] | None = None
        for i, it in enumerate(children):
            if it.objectName() == "qt_msgbox_label":
                # Qt stubs are wrong about this return value
                position = grid.getItemPosition(i)  # type: ignore[assignment]
                old_label = typing.cast("QtWidgets.QLabel", it)
                break
        assert old_label is not None
        assert position is not None

        label = QtWidgets.QLabel(old_label.text(), self)
        label.setWordWrap(True)
        label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        label.setCursor(QtCore.Qt.CursorShape.IBeamCursor)
        self.label = label

        scroll = QtWidgets.QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setWidget(label)
        scroll.setMinimumSize(400, 200)
        grid.addWidget(scroll, *position)
        self.scroll_area = scroll

        old_label.setText("")

        if default_button is not None:
            if not buttons & default_button:
                raise ValueError(f"Default button {default_button} is not present in {buttons}")
            self.setDefaultButton(default_button)

    def text(self) -> str:
        return self.label.text()

    def setText(self, text: str) -> None:
        self.label.setText(text)

    @classmethod
    def create_new(
        cls,
        parent: QtWidgets.QWidget,
        icon: QtWidgets.QMessageBox.Icon,
        title: str,
        body: str,
        buttons: QtWidgets.QMessageBox.StandardButton,
        default_button: QtWidgets.QMessageBox.StandardButton = QtWidgets.QMessageBox.StandardButton.Ok,
    ) -> ScrollMessageBox:
        box = cls(icon, title, body, buttons, parent)
        box.setDefaultButton(default_button)
        return box
