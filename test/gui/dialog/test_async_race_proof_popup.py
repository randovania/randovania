from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6 import QtWidgets

from randovania.gui.dialog.async_race_proof_popup import AsyncRaceProofPopup

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot


def test_getters(skip_qtbot: QtBot) -> None:
    parent = QtWidgets.QMainWindow()
    skip_qtbot.add_widget(parent)

    dialog = AsyncRaceProofPopup(parent)

    dialog.ui.notes_edit.setPlainText("here's the notes")

    dialog.ui.proof_edit.setText("fooBar")
    assert not dialog.ui.button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Save).isEnabled()

    dialog.ui.proof_edit.setText("https://www.youtube.com")
    assert dialog.ui.button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Save).isEnabled()

    assert dialog.submission_notes == "here's the notes"
    assert dialog.proof_url == "https://www.youtube.com"
