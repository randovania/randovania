from PySide6 import QtWidgets, QtCore

from randovania.gui.widgets.delayed_text_label import DelayedTextLabel


class ChangeLogWidget(QtWidgets.QTabWidget):
    def __init__(self, all_change_logs: dict[str, str]):
        super().__init__()
        # VerticalTabBar doesn't work as expected in Qt 6, so it's disabled for now
        # self.setTabBar(VerticalTabBar())
        self.setTabPosition(QtWidgets.QTabWidget.West)
        self.tabBar().setUsesScrollButtons(True)
        self.tabBar().setElideMode(QtCore.Qt.ElideNone)

        for version_name, version_text in all_change_logs.items():
            scroll_area = QtWidgets.QScrollArea()
            scroll_area.setObjectName(f"scroll_area {version_name}")
            scroll_area.setWidgetResizable(True)

            label = DelayedTextLabel()
            label.setAlignment(QtCore.Qt.AlignTop)
            label.setObjectName(f"label {version_name}")
            label.setTextFormat(QtCore.Qt.MarkdownText)
            label.setText(version_text)
            label.setWordWrap(True)

            scroll_area.setWidget(label)
            self.addTab(scroll_area, version_name)
