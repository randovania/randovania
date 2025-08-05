from __future__ import annotations

from typing import Any

from randovania.gui.dialog.connector_prompt_dialog import ConnectorPromptDialog


class MSRConnectorPromptDialog(ConnectorPromptDialog):
    def __init__(self, **kwargs: dict[str, Any]) -> None:
        super().__init__(**kwargs)

        self.top_radio.setText("Azahar")
        self.top_label.setText("Connects to Azahar running on this computer.")

        self.ip_radio.setText("Luma3DS")
