from __future__ import annotations

from typing import cast

from PySide6 import QtCore, QtWidgets

from randovania.gui.widgets.delayed_text_label import DelayedTextLabel


class ChangeLogWidget(QtWidgets.QWidget):
    def __init__(self, all_change_logs: dict[str, str]) -> None:
        super().__init__()

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.select_version = QtWidgets.QComboBox(self)
        self.select_version.setMaxVisibleItems(10)

        # TODO: QComboBox does not display scrollbar for Linux/MacOS
        self.select_version.setStyleSheet(
            "QComboBox { combobox-popup: 0; }"
        )  # HACK: Done to respect max items limit on Linux/macOS
        self.select_version.currentIndexChanged.connect(self.select_version_index_changed)

        layout.addWidget(self.select_version)

        self.changelog = QtWidgets.QStackedWidget(self)
        layout.addWidget(self.changelog)

        for version_name, version_text in all_change_logs.items():
            scroll_area = QtWidgets.QScrollArea()
            scroll_area.setObjectName(f"scroll_area {version_name}")
            scroll_area.setWidgetResizable(True)

            label = DelayedTextLabel()
            label.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
            label.setObjectName(f"label {version_name}")
            label.setOpenExternalLinks(True)
            label.setTextFormat(QtCore.Qt.TextFormat.MarkdownText)
            label.setText(version_text)
            label.setWordWrap(True)

            scroll_area.setWidget(label)
            self.changelog.addWidget(scroll_area)

            self.select_version.addItem(version_name)

        self.changelog.setCurrentIndex(0)

    def select_version_index_changed(self) -> None:
        selected_widget = cast(
            QtWidgets.QScrollArea,
            self.findChild(QtWidgets.QScrollArea, f"scroll_area {self.select_version.currentText()}"),
        )

        self.changelog.setCurrentWidget(selected_widget)
