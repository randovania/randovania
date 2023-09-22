from __future__ import annotations

import typing

from PySide6 import QtWidgets

from randovania.gui.generated.text_prompt_dialog_ui import Ui_TextPromptDialog
from randovania.gui.lib import async_dialog, common_qt_lib


class TextPromptDialog(QtWidgets.QDialog, Ui_TextPromptDialog):
    def __init__(
        self,
        parent: QtWidgets.QWidget | None,
        title: str,
        description: str,
        *,
        is_modal: bool,
        initial_value: str | None,
        max_length: int | None,
        is_password: bool,
        check_re: typing.Pattern | None,
    ):
        super().__init__(parent)
        self.setupUi(self)
        common_qt_lib.set_default_window_icon(self)

        self.setWindowTitle(title)
        self.description_label.setText(description)
        self.setModal(is_modal)
        self.check_re = check_re

        self.accept_button.setEnabled(False)
        self.accept_button.setDefault(True)
        self.accept_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        if initial_value is not None:
            self.prompt_edit.setText(initial_value)

        if is_password:
            self.prompt_edit.setEchoMode(QtWidgets.QLineEdit.EchoMode.PasswordEchoOnEdit)

        if max_length is not None:
            self.prompt_edit.setMaxLength(max_length)

        self.prompt_edit.textChanged.connect(self._on_text_changed)
        self.prompt_edit.setFocus()

    @property
    def text_value(self) -> str:
        return self.prompt_edit.text().strip()

    def _on_text_changed(self, value: str):
        error_message = None

        if self.check_re is not None:
            if self.check_re.match(self.text_value) is None:
                error_message = "Input does not match rules"
        elif not self.text_value:
            error_message = "Input required"

        common_qt_lib.set_error_border_stylesheet(self.prompt_edit, error_message is not None)
        self.accept_button.setEnabled(error_message is None)
        self.error_label.setText(error_message or "")

    @classmethod
    async def prompt(
        cls,
        *,
        title: str,
        description: str,
        parent: QtWidgets.QWidget | None = None,
        max_length: int | None = None,
        is_password: bool = False,
        initial_value: str | None = None,
        is_modal: bool = False,
        check_re: typing.Pattern | None = None,
    ) -> str | None:
        inst = cls(
            parent=parent,
            title=title,
            description=description,
            max_length=max_length,
            initial_value=initial_value,
            is_password=is_password,
            is_modal=is_modal,
            check_re=check_re,
        )

        if await async_dialog.execute_dialog(inst) == QtWidgets.QDialog.DialogCode.Accepted:
            return inst.text_value
        else:
            return None
