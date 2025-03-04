from __future__ import annotations

import re

from PySide6 import QtWidgets

from randovania.gui.generated.async_race_proof_popup_ui import Ui_AsyncRaceProof
from randovania.gui.lib import common_qt_lib


class AsyncRaceProofPopup(QtWidgets.QDialog):
    """Popup for the user to enter a Proof URL and some submission notes for their Async Race result."""

    ui: Ui_AsyncRaceProof

    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)
        self.ui = Ui_AsyncRaceProof()
        self.ui.setupUi(self)
        common_qt_lib.set_default_window_icon(self)

        self._proof_re = re.compile(r"https?://.+")
        self.ui.button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Save).setEnabled(False)

        # Signals
        self.ui.button_box.accepted.connect(self.accept)
        self.ui.button_box.rejected.connect(self.reject)
        self.ui.proof_edit.textChanged.connect(self._on_proof_updated)

    def _on_proof_updated(self) -> None:
        """Validate that the proof URL at least looks like a URL"""
        common_qt_lib.set_error_border_stylesheet(self.ui.proof_edit, self._proof_re.match(self.proof_url) is None)
        self.ui.button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Save).setEnabled(
            not self.ui.proof_edit.has_error
        )

    @property
    def proof_url(self) -> str:
        """The proof URL entered by the user"""
        return self.ui.proof_edit.text()

    @property
    def submission_notes(self) -> str:
        """The submission notes entered by the user"""
        return self.ui.notes_edit.toPlainText()
