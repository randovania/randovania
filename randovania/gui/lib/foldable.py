from __future__ import annotations

from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import Property, Qt, Signal


class Foldable(QtWidgets.QWidget):
    _main_layout: QtWidgets.QGridLayout
    _toggle_button: QtWidgets.QToolButton
    _header_line: QtWidgets.QFrame
    _content_area: QtWidgets.QFrame
    _folded: bool

    def __init__(self, parent: QtWidgets.QWidget | None, title: str = "", initially_folded: bool = True):
        super().__init__(parent)

        self._folded = initially_folded

        self._toggle_button = QtWidgets.QToolButton(self)
        self._toggle_button.setStyleSheet("QToolButton { height: 30px; padding: 0px; }")
        font = self._toggle_button.font()
        font.setBold(True)
        font.setPixelSize(13)
        self._toggle_button.setFont(font)
        self._toggle_button.setMaximumHeight(30)
        self._toggle_button.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self._toggle_button.setArrowType(QtCore.Qt.ArrowType.RightArrow)
        self._toggle_button.setText(title)
        self._toggle_button.setCheckable(True)
        self._toggle_button.setChecked(False)
        self._toggle_button.clicked.connect(self._on_click)

        self._header_line = QtWidgets.QFrame(self)
        self._header_line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        self._header_line.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Maximum)

        self._content_area = QtWidgets.QFrame(self)
        self._content_area.setObjectName("foldable_contentArea")
        self._content_area.setStyleSheet("#foldable_contentArea { border: none; }")
        self._content_area.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)

        self._main_layout = QtWidgets.QGridLayout(self)
        self._main_layout.setVerticalSpacing(0)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.addWidget(self._toggle_button, 0, 0, 1, 1, Qt.AlignLeft)
        self._main_layout.addWidget(self._header_line, 0, 1, 1, 1)
        self._main_layout.addWidget(self._content_area, 1, 0, 1, 2)

    @property
    def contents(self):
        return self._content_area

    def _on_click(self, checked: bool):
        self.setFolded(not self._folded)

    def _unfold(self):
        self._folded = False
        self._content_area.show()
        self._toggle_button.setArrowType(Qt.ArrowType.DownArrow)

    def _fold(self):
        self._folded = True
        self._content_area.hide()
        self._toggle_button.setArrowType(Qt.ArrowType.RightArrow)

    def set_content_layout(self, content_layout: QtWidgets.QLayout):
        self._content_area.setLayout(content_layout)
        if self._folded:
            self._fold()
        else:
            self._unfold()

    def setTitle(self, title: str):
        self._toggle_button.setText(title)

    def setFolded(self, folded: bool):
        if folded:
            self._fold()
        else:
            self._unfold()

    @Signal
    def notify(self):
        pass

    folded = Property(
        bool,
        fset=setFolded,
        notify=notify,
    )
    title = Property(
        str,
        fset=setTitle,
        notify=notify,
    )
