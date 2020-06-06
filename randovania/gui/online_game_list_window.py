from typing import List

from PySide2.QtCore import Qt
from PySide2.QtWidgets import QPushButton, QDialogButtonBox, QDialog, QTableWidgetItem, QInputDialog, QLineEdit, \
    QMessageBox
from asyncqt import asyncSlot

from randovania.gui.generated.game_session_browser_dialog_ui import Ui_GameSessionBrowserDialog
from randovania.gui.lib import common_qt_lib
from randovania.network_client.game_session import GameSessionListEntry
from randovania.network_common.error import WrongPassword


class GameSessionBrowserDialog(QDialog, Ui_GameSessionBrowserDialog):
    sessions: List[GameSessionListEntry]

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        common_qt_lib.set_default_window_icon(self)

        self.refresh_button = QPushButton("Refresh")
        self.button_box.addButton(self.refresh_button, QDialogButtonBox.ResetRole)
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
        self.button_box.button(QDialogButtonBox.Ok).setText("Join")

        self.button_box.accepted.connect(self.attempt_join)
        self.button_box.rejected.connect(self.reject)
        self.refresh_button.clicked.connect(self.refresh)

        self.table_widget.itemSelectionChanged.connect(self.on_selection_changed)
        self.table_widget.itemDoubleClicked.connect(self.on_double_click)

    @asyncSlot()
    async def refresh(self):
        self.refresh_button.setEnabled(False)
        try:
            self.sessions = await common_qt_lib.get_network_client().get_game_session_list()
            self.update_list()
        finally:
            self.refresh_button.setEnabled(True)

    def on_selection_changed(self):
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(len(self.table_widget.selectedItems()) > 0)

    @property
    def selected_session(self):
        row: int = self.table_widget.selectedIndexes()[0].row()
        return self.sessions[row]

    @asyncSlot(QTableWidgetItem)
    async def on_double_click(self, item: QTableWidgetItem):
        await self.attempt_join()

    @asyncSlot()
    async def attempt_join(self):
        if not self.sessions:
            return

        session = self.selected_session

        if session.has_password:
            dialog = QInputDialog(self)
            # dialog.setWindowFlags(dialog.windowFlags() & ~Qt::WindowContextHelpButtonHint)
            dialog.setWindowTitle("Enter password")
            dialog.setLabelText("This session requires a password:")
            dialog.setWindowModality(Qt.WindowModal)
            dialog.setTextEchoMode(QLineEdit.Password)

            if dialog.exec_() != dialog.Accepted:
                return

            password = dialog.textValue()
        else:
            password = None

        try:
            await common_qt_lib.get_network_client().join_session(session, password)
            return self.accept()

        except WrongPassword:
            QMessageBox.warning(self,
                                "Incorrect Password",
                                "The password entered was incorrect.")

    def update_list(self):
        self.table_widget.clear()
        self.table_widget.setHorizontalHeaderLabels(["Name", "Password?", "In-Game", "Type", "Players"])

        self.table_widget.setRowCount(len(self.sessions))
        for i, session in enumerate(self.sessions):
            name = QTableWidgetItem(session.name)
            has_password = QTableWidgetItem("Yes" if session.has_password else "No")
            in_game = QTableWidgetItem("Yes" if session.in_game else "No")
            type_item = QTableWidgetItem("Race")
            players_item = QTableWidgetItem(str(session.num_players))

            self.table_widget.setItem(i, 0, name)
            self.table_widget.setItem(i, 1, has_password)
            self.table_widget.setItem(i, 2, in_game)
            self.table_widget.setItem(i, 3, type_item)
            self.table_widget.setItem(i, 4, players_item)

        self.status_label.setText(f"{len(self.sessions)} sessions found")
