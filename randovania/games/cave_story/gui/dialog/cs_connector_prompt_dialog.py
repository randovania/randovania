from __future__ import annotations

import typing
from typing import TYPE_CHECKING

from randovania.gui.dialog.connector_prompt_dialog import ConnectorPromptDialog

if TYPE_CHECKING:
    from PySide6 import QtWidgets


class CSConnectorPromptDialog(ConnectorPromptDialog):
    def __init__(
        self,
        parent: QtWidgets.QWidget | None,
        title: str,
        description: str,
        max_length: int | None = None,
        is_password: bool = False,
        initial_value: str | None = None,
        is_modal: bool = False,
        check_re: typing.Pattern | None = None,
    ) -> None:
        super().__init__(
            parent=parent,
            title=title,
            description=description,
            max_length=max_length,
            initial_value=initial_value,
            is_password=is_password,
            is_modal=is_modal,
            check_re=check_re,
        )

        self.top_radio.setText("Standard")
        self.top_label.setText("Connects to a copy of Cave Story running on this computer.")

        self.ip_radio.setText("Custom IP Address")
