from PySide2.QtCore import Qt
from PySide2.QtWidgets import QGridLayout, QLayout, QToolButton, QVBoxLayout, QWidget, QFrame, QScrollArea, QSizePolicy

class Foldable(QWidget):
    _mainLayout: QGridLayout
    _toggleButton: QToolButton
    _headerLine: QFrame
    _contentArea: QScrollArea
    _folded: bool

    def __init__(self, title: str, initially_folded: bool = True, parent: QWidget = None):
        super().__init__(parent)

        self._folded = initially_folded

        self._toggleButton = QToolButton(self)
        self._toggleButton.setStyleSheet("QToolButton { height: 20px; }")
        font = self._toggleButton.font()
        font.setBold(True)
        font.setPixelSize(13)
        self._toggleButton.setFont(font)
        self._toggleButton.setMaximumHeight(20)
        self._toggleButton.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self._toggleButton.setArrowType(Qt.ArrowType.RightArrow)
        self._toggleButton.setText(title)
        self._toggleButton.setCheckable(True)
        self._toggleButton.setChecked(False)
        self._toggleButton.clicked.connect(self._on_click)

        self._headerLine = QFrame(self)
        self._headerLine.setFrameShape(QFrame.HLine)
        self._headerLine.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

        self._contentArea = QFrame(self)
        self._contentArea.setObjectName("foldable_contentArea")
        self._contentArea.setStyleSheet("#foldable_contentArea { border: none; }")
        self._contentArea.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        self._mainLayout = QGridLayout(self)
        self._mainLayout.setVerticalSpacing(0)
        self._mainLayout.setContentsMargins(0, 0, 0, 0)
        self._mainLayout.addWidget(self._toggleButton, 0, 0, 1, 1, Qt.AlignLeft)
        self._mainLayout.addWidget(self._headerLine, 0, 1, 1, 1)
        self._mainLayout.addWidget(self._contentArea, 1, 0, 1, 2)

    @property
    def contents(self):
        return self._contentArea

    def _on_click(self, checked: bool):
        if self._folded:
            self._unfold()   
        else:
            self._fold()

    def _unfold(self):
        self._folded = False
        self._contentArea.show()
        self._toggleButton.setArrowType(Qt.ArrowType.DownArrow)

    def _fold(self):
        self._folded = True
        self._contentArea.hide()
        self._toggleButton.setArrowType(Qt.ArrowType.RightArrow)

    def set_content_layout(self, content_layout: QLayout):
        self._contentArea.setLayout(content_layout)
        if self._folded:
            self._fold()
        else:
            self._unfold()
