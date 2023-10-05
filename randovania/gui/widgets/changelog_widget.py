from __future__ import annotations

import re
from typing import cast

import requests
from PySide6 import QtCore, QtGui, QtWidgets

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

            frame = QtWidgets.QFrame()
            frame.setContentsMargins(0, 0, 0, 0)

            frame_layout = QtWidgets.QVBoxLayout()
            frame_layout.setContentsMargins(0, 0, 0, 0)
            frame.setLayout(frame_layout)

            images = self.image_parse(version_text)

            if images is not None:
                for widget in images:
                    if widget.pixmap().isNull():
                        self.setup_delayed_text_label(widget)

                    frame_layout.addWidget(widget)
            else:
                label = DelayedTextLabel(text=version_text)
                self.setup_delayed_text_label(label)

                frame_layout.addWidget(label)

            scroll_area.setWidget(frame)
            self.changelog.addWidget(scroll_area)

            self.select_version.addItem(version_name)

        self.changelog.setCurrentIndex(0)

    def select_version_index_changed(self) -> None:
        selected_widget = cast(
            QtWidgets.QScrollArea,
            self.findChild(QtWidgets.QScrollArea, f"scroll_area {self.select_version.currentText()}"),
        )

        self.changelog.setCurrentWidget(selected_widget)

    def setup_delayed_text_label(self, label: DelayedTextLabel) -> None:
        label.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        label.setOpenExternalLinks(True)
        label.setTextFormat(QtCore.Qt.TextFormat.MarkdownText)
        label.setWordWrap(True)

    def image_parse(self, version_text: str) -> list[DelayedTextLabel] | None:
        links: list[str] = re.findall(r"!\[image\][^)]+", version_text)

        if links:
            new_version_text: list[DelayedTextLabel] = []
            version_text_splitlines = version_text.splitlines()

            for link in links:
                parsed_link = link[9:]

                # Regex pattern removes the ending parenthesis
                line_index = version_text_splitlines.index(link + ")")

                # Recreate markdown up to the current (not including) ![image] iter index
                version_text_part: str = "\n".join(version_text_splitlines[:line_index])

                # Remove all lines before and including ![image] link
                version_text_splitlines = version_text_splitlines[line_index + 1 :]

                version_text_part_label = DelayedTextLabel(text=version_text_part)

                new_version_text.append(version_text_part_label)

                try:
                    image_data = requests.get(parsed_link)
                    image_data.raise_for_status()
                except requests.HTTPError as e:
                    new_version_text.append(DelayedTextLabel(text=f"{e}"))
                    continue

                image = QtGui.QImage()
                image.loadFromData(image_data.content)

                image_label = DelayedTextLabel()
                image_label.setPixmap(QtGui.QPixmap(image))

                new_version_text.append(image_label)

            # Checking to see if theres remaining markdown text after the images
            if version_text_splitlines:
                new_version_text.append(DelayedTextLabel(text="\n".join(version_text_splitlines)))

            return new_version_text
