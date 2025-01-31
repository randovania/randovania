from __future__ import annotations

from typing import Any

from PySide6 import QtWidgets

from randovania.gui.dialog.text_prompt_dialog import TextPromptDialog
from randovania.gui.lib import async_dialog


class DolphinConnectorPromptDialog(TextPromptDialog):
    """Similar to ConnectorPromptDialog, but with more options."""

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)

        # Top line: Launch & Autodetect radio buttons
        self.launch = QtWidgets.QRadioButton("Launch", self)
        self.launch.setToolTip(
            "Run a custom command under Randovania's control, then connect to it. "
            "This may be needed to work on Linux systems with default security settings."
        )
        self.autodetect = QtWidgets.QRadioButton("Autodetect", self)
        self.autodetect.setToolTip("Attempt to find and connect to an already running Dolphin.")
        self.gridLayout.addWidget(self.autodetect, 1, 0, 1, 1)
        self.gridLayout.addWidget(self.launch, 1, 1, 1, 2)

        # Next line, Run Command radio button, text field
        self.cmd_label = QtWidgets.QLabel("Command", self)
        self.prompt_edit.setToolTip(
            "The command to run. This can either be an absolute path (e.g. /usr/bin/dolphin-emu) "
            "or a plain command name (e.g. dolphin-emu)."
        )
        self.gridLayout.addWidget(self.cmd_label, 2, 0, 1, 1)
        self.gridLayout.addWidget(self.prompt_edit, 2, 1, 1, 2)

        # Third line, custom commname search
        self.comm_label = QtWidgets.QLabel("Search", self)
        self.comm_edit = QtWidgets.QLineEdit("", self)
        self.comm_edit.setToolTip(
            "The program name to search for when connecting. Leave blank to use the default "
            "for whatever system you are on. Dolphin on NixOS requires '.dolphin-emu-wr' here."
        )
        self.gridLayout.addWidget(self.comm_label, 3, 0, 1, 1)
        self.gridLayout.addWidget(self.comm_edit, 3, 1, 1, 2)

        # Move around stuff from TextPromptDialog that no longer fits in its
        # original position.
        self.gridLayout.addWidget(self.description_label, 4, 0, 1, 3)
        self.gridLayout.addWidget(self.error_label, 6, 1, 1, 1)

        self.launch.toggled.connect(self._select_launch)
        self.autodetect.toggled.connect(self._select_autodetect)
        self.autodetect.setChecked(True)

        self.description_label.setText(
            "On Windows, the default of 'Autodetect' should work for most users. "
            "If you are running Linux, you may need to experiment with these settings somewhat -- "
            "mouse over the options for more information."
        )

        self.description_label.setWordWrap(True)
        self.gridLayout.setColumnStretch(1, 1)
        self._auto_resize()

    def _auto_resize(self) -> None:
        # The text_prompt_dialog.ui file has hardcoded dimensions which may be too
        # small for this dialog, so recompute it whenever we hide/show elements.
        self.resize(self.width(), self.sizeHint().height())

    def _select_autodetect(self) -> None:
        self.cmd_label.hide()
        self.prompt_edit.hide()
        self.comm_label.hide()
        self.comm_edit.hide()
        self.accept_button.setEnabled(True)
        self.error_label.setText("")

    def _select_launch(self) -> None:
        self.cmd_label.show()
        self.prompt_edit.show()
        self.comm_label.show()
        self.comm_edit.show()
        self._on_text_changed("")

    @property
    def value(self) -> (str, str):
        return (self.prompt_edit.text().strip(), self.comm_edit.text().strip())

    @classmethod
    async def prompt(
        cls,
        *,
        parent: QtWidgets.QWidget | None = None,
        is_modal: bool = False,
    ) -> (str, str) | None:
        inst = cls(
            parent=parent,
            is_modal=is_modal,
            title="Configure Dolphin Connection",
            description="",
            max_length=None,
            initial_value=None,
            is_password=False,
            check_re=None,
        )

        if await async_dialog.execute_dialog(inst) == QtWidgets.QDialog.DialogCode.Accepted:
            return inst.value
        else:
            return None
