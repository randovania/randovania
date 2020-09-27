from typing import List

from PySide2.QtCore import Qt
from PySide2.QtWidgets import QPushButton, QDialogButtonBox, QDialog, QTableWidgetItem, QInputDialog, QLineEdit
from asyncqt import asyncSlot

from randovania.gui.generated.game_session_browser_dialog_ui import Ui_GameSessionBrowserDialog
from randovania.gui.lib import common_qt_lib, async_dialog
from randovania.gui.lib.qt_network_client import handle_network_errors, QtNetworkClient
from randovania.network_client.game_session import GameSessionListEntry
from randovania.network_client.network_client import ConnectionState
from randovania.network_common.error import WrongPassword
from randovania.network_common.session_state import GameSessionState


class GameSessionBrowserDialog(QDialog, Ui_GameSessionBrowserDialog):
    sessions: List[GameSessionListEntry]

    def __init__(self, network_client: QtNetworkClient):
        super().__init__()
        self.setupUi(self)
        common_qt_lib.set_default_window_icon(self)
        self.network_client = network_client

        self.refresh_button = QPushButton("Refresh")
        self.button_box.addButton(self.refresh_button, QDialogButtonBox.ResetRole)
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
        self.button_box.button(QDialogButtonBox.Ok).setText("Join")

        self.button_box.accepted.connect(self.attempt_join)
        self.button_box.rejected.connect(self.reject)
        self.refresh_button.clicked.connect(self.refresh)

        checks = (
            self.has_password_yes_check,
            self.has_password_no_check,
            self.state_setup_check,
            self.state_inprogress_check,
            self.state_finished_check,
        )
        for check in checks:
            check.stateChanged.connect(self.update_list)
        self.filter_name_edit.textEdited.connect(self.update_list)

        self.table_widget.itemSelectionChanged.connect(self.on_selection_changed)
        self.table_widget.itemDoubleClicked.connect(self.on_double_click)

        self.network_client.ConnectionStateUpdated.connect(self.on_server_connection_state_updated)
        self.on_server_connection_state_updated(self.network_client.connection_state)

    @asyncSlot()
    @handle_network_errors
    async def refresh(self):
        self.refresh_button.setEnabled(False)
        try:
            self.sessions = await self.network_client.get_game_session_list()
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
    @handle_network_errors
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

            if await async_dialog.execute_dialog(dialog) != dialog.Accepted:
                return

            password = dialog.textValue()
        else:
            password = None

        try:
            await self.network_client.join_game_session(session, password)
            return self.accept()

        except WrongPassword:
            await async_dialog.warning(self, "Incorrect Password", "The password entered was incorrect.")

    def update_list(self):
        self.table_widget.clear()
        self.table_widget.setHorizontalHeaderLabels(["Name", "Password?", "In-Game", "Type", "Players"])

        name_filter = self.filter_name_edit.text().strip()

        displayed_has_password = set()
        if self.has_password_yes_check.isChecked():
            displayed_has_password.add(True)
        if self.has_password_no_check.isChecked():
            displayed_has_password.add(False)

        displayed_states = set()
        for (check, state) in ((self.state_setup_check, GameSessionState.SETUP),
                               (self.state_inprogress_check, GameSessionState.IN_PROGRESS),
                               (self.state_finished_check, GameSessionState.FINISHED)):
            if check.isChecked():
                displayed_states.add(state)

        visible_sessions = [
            session
            for session in self.sessions
            if (session.has_password in displayed_has_password
                and session.state in displayed_states
                and name_filter in session.name)
        ]

        self.table_widget.setRowCount(len(visible_sessions))
        for i, session in enumerate(visible_sessions):
            name = QTableWidgetItem(session.name)
            state = QTableWidgetItem(session.state.user_friendly_name)
            players_item = QTableWidgetItem(str(session.num_players))
            has_password = QTableWidgetItem("Yes" if session.has_password else "No")
            creator = QTableWidgetItem(session.creator)

            self.table_widget.setItem(i, 0, name)
            self.table_widget.setItem(i, 1, state)
            self.table_widget.setItem(i, 2, players_item)
            self.table_widget.setItem(i, 3, has_password)
            self.table_widget.setItem(i, 4, creator)

        self.status_label.setText(f"{len(self.sessions)} sessions total, {len(visible_sessions)} displayed.")

    def on_server_connection_state_updated(self, state: ConnectionState):
        self.server_connection_label.setText(f"Server: {state.value}")
