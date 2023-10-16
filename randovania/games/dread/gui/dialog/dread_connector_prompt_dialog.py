from __future__ import annotations

from typing import Any

from PySide6 import QtWidgets

from randovania.gui.dialog.text_prompt_dialog import TextPromptDialog


class DreadConnectorPromptDialog(TextPromptDialog):
    def __init__(self, **kwargs: dict[str, Any]):
        super().__init__(**kwargs)

        self.ryujinx_radio = QtWidgets.QRadioButton("Ryujinx", self)
        self.ryujinx_label = QtWidgets.QLabel("Connects to a Ryujinx running on this computer.", self)
        self.gridLayout.addWidget(self.ryujinx_radio, 1, 0, 1, 3)
        self.gridLayout.addWidget(self.ryujinx_label, 2, 0, 1, 3)

        self.ip_radio = QtWidgets.QRadioButton("Switch", self)
        self.gridLayout.addWidget(self.ip_radio, 3, 0, 1, 1)
        self.gridLayout.addWidget(self.prompt_edit, 3, 1, 1, 2)
        self.gridLayout.addWidget(self.description_label, 4, 0, 1, 3)
        self.gridLayout.addWidget(self.error_label, 6, 1, 1, 1)

        self.ryujinx_radio.toggled.connect(self._select_ryujinx)
        self.ip_radio.toggled.connect(self._select_ip)
        self.ryujinx_radio.setChecked(True)

    def _select_ryujinx(self):
        self.prompt_edit.setEnabled(False)
        self.accept_button.setEnabled(True)

    def _select_ip(self):
        self.prompt_edit.setEnabled(True)
        self._on_text_changed("")

    @property
    def text_value(self) -> str:
        if self.ryujinx_radio.isChecked():
            return "localhost"
        else:
            return self.prompt_edit.text().strip()


class CSConnectorPromptDialog(DreadConnectorPromptDialog):
    def __init__(self, **kwargs: dict[str, Any]) -> None:
        super().__init__(**kwargs)

        self.ryujinx_radio.setText("Standard")
        self.ryujinx_label.setText("Connects to a copy of Cave Story running on this computer.")

        self.ip_radio.setText("Custom IP Address")
