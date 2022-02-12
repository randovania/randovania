from PySide2 import QtWidgets, QtCore


def _update_label_on_show(label: QtWidgets.QLabel, text: str):
    def showEvent(_):
        if label._delayed_text is not None:
            label.setText(label._delayed_text)
            label._delayed_text = None

    label._delayed_text = text
    label.showEvent = showEvent


class ChangeLogWidget(QtWidgets.QWidget):
    def __init__(self, all_change_logs: list[str]):
        super().__init__()

        self.setObjectName("changelog_tab")

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setObjectName("changelog_tab_layout")

        self.scroll_area = QtWidgets.QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setObjectName("changelog_scroll_area")

        self.scroll_contents = QtWidgets.QWidget()
        self.scroll_contents.setGeometry(QtCore.QRect(0, 0, 489, 337))
        self.scroll_contents.setObjectName("changelog_scroll_contents")
        self.scroll_layout = QtWidgets.QVBoxLayout(self.scroll_contents)
        self.scroll_layout.setObjectName("changelog_scroll_layout")

        for entry in all_change_logs:
            changelog_label = QtWidgets.QLabel(self.scroll_contents)
            changelog_label.setTextFormat(QtCore.Qt.MarkdownText)
            _update_label_on_show(changelog_label, entry)
            changelog_label.setObjectName("changelog_label")
            changelog_label.setWordWrap(True)
            self.scroll_layout.addWidget(changelog_label)

        self.scroll_area.setWidget(self.scroll_contents)
        self.layout.addWidget(self.scroll_area)
