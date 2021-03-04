import pypresence
from PySide2 import QtWidgets
from PySide2.QtWidgets import QDialog
from qasync import asyncSlot

from randovania.gui.generated.login_prompt_dialog_ui import Ui_LoginPromptDialog
from randovania.gui.lib import common_qt_lib, async_dialog
from randovania.gui.lib.qt_network_client import QtNetworkClient, handle_network_errors
from randovania.network_client.game_session import User
from randovania.network_client.network_client import ConnectionState


class LoginPromptDialog(QDialog, Ui_LoginPromptDialog):

    def __init__(self, network_client: QtNetworkClient):
        super().__init__()
        self.setupUi(self)
        common_qt_lib.set_default_window_icon(self)
        self.network_client = network_client

        login_methods = network_client.available_login_methods
        self.guest_button.setVisible("guest" in login_methods)
        self.discord_button.setEnabled("discord" in login_methods)
        self.discord_button.setToolTip(
            ""
            if self.discord_button.isEnabled() else
            "This Randovania build is not configured to login with Discord."
        )
        self.privacy_policy_label.setText(self.privacy_policy_label.text().replace("color:#0000ff;", ""))

        self.button_box.button(QtWidgets.QDialogButtonBox.Reset).setText("Logout")

        # Signals
        self.network_client.ConnectionStateUpdated.connect(self.on_server_connection_state_updated)
        self.network_client.UserChanged.connect(self.on_user_changed)

        self.guest_button.clicked.connect(self.on_login_as_guest_button)
        self.discord_button.clicked.connect(self.on_login_with_discord_button)
        self.button_box.button(QtWidgets.QDialogButtonBox.Ok).clicked.connect(self.on_ok_button)
        self.button_box.button(QtWidgets.QDialogButtonBox.Reset).clicked.connect(self.on_logout_button)

        # Initial update
        self.on_user_changed(network_client.current_user)

    def on_user_changed(self, user: User):
        self.on_server_connection_state_updated(self.network_client.connection_state)
        self.button_box.button(QtWidgets.QDialogButtonBox.Reset).setEnabled(user is not None)

    def on_server_connection_state_updated(self, state: ConnectionState):
        message = f"{state.value}"
        if state == ConnectionState.Connected:
            message += f", logged as {self.network_client.current_user.name}"
        elif self.network_client.has_previous_session():
            message += " (with saved session)"

        self.connection_status_label.setText(message)

    @asyncSlot()
    @handle_network_errors
    async def on_login_as_guest_button(self):
        dialog = QtWidgets.QInputDialog(self)
        dialog.setModal(True)
        dialog.setWindowTitle("Enter guest name")
        dialog.setLabelText("Select a name for the guest account:")
        if await async_dialog.execute_dialog(dialog) != dialog.Accepted:
            return

        await self.network_client.login_as_guest(dialog.textValue())

    @asyncSlot()
    @handle_network_errors
    async def on_login_with_discord_button(self):
        try:
            await self.network_client.login_with_discord()
        except pypresence.exceptions.InvalidPipe:
            await async_dialog.warning(self, "Discord login",
                                       "Login failed. Is Discord running?")
        except pypresence.exceptions.ServerError:
            await async_dialog.warning(self, "Discord login",
                                       "Login failed. Did you reject the authorization prompt in Discord?")

    def on_ok_button(self):
        self.accept()

    @asyncSlot()
    @handle_network_errors
    async def on_logout_button(self):
        await self.network_client.logout()
