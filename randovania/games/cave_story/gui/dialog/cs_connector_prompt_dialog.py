from __future__ import annotations

from typing import Any

from randovania.gui.dialog.connector_prompt_dialog import ConnectorPromptDialog


class CSConnectorPromptDialog(ConnectorPromptDialog):
    def __init__(self, **kwargs: dict[str, Any]) -> None:
        super().__init__(**kwargs)

        self.top_radio.setText("Standard")
        self.top_label.setText("Connects to a copy of Cave Story running on this computer.")

        self.ip_radio.setText("Custom IP Address")
