from __future__ import annotations

from typing import Any

from PySide6 import QtWidgets

from randovania.gui.dialog.text_prompt_dialog import TextPromptDialog


class ConnectorPromptDialog(TextPromptDialog):
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)

        self.top_radio = QtWidgets.QRadioButton("Top", self)
        self.top_label = QtWidgets.QLabel("Top Label", self)
        self.gridLayout.addWidget(self.top_radio, 1, 0, 1, 3)
        self.gridLayout.addWidget(self.top_label, 2, 0, 1, 3)

        self.ip_radio = QtWidgets.QRadioButton("IP radio", self)
        self.gridLayout.addWidget(self.ip_radio, 3, 0, 1, 1)
        self.gridLayout.addWidget(self.prompt_edit, 3, 1, 1, 2)
        self.gridLayout.addWidget(self.description_label, 4, 0, 1, 3)
        self.gridLayout.addWidget(self.error_label, 6, 1, 1, 1)

        self.top_radio.toggled.connect(self._select_top)
        self.ip_radio.toggled.connect(self._select_ip)
        self.top_radio.setChecked(True)

    def _select_top(self) -> None:
        self.prompt_edit.setEnabled(False)
        self.accept_button.setEnabled(True)

    def _select_ip(self) -> None:
        self.prompt_edit.setEnabled(True)
        self._on_text_changed("")

    @property
    def text_value(self) -> str:
        if self.top_radio.isChecked():
            return "localhost"
        else:
            return self.prompt_edit.text().strip()
