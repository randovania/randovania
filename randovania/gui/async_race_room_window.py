import datetime

import humanize
from PySide6 import QtCore, QtWidgets
from qasync import asyncSlot

from randovania.gui import game_specific_gui
from randovania.gui.dialog.async_race_admin_dialog import AsyncRaceAdminDialog
from randovania.gui.dialog.async_race_leaderboard_dialog import AsyncRaceLeaderboardDialog
from randovania.gui.dialog.async_race_proof_popup import AsyncRaceProofPopup
from randovania.gui.dialog.async_race_settings_dialog import AsyncRaceSettingsDialog
from randovania.gui.generated.async_race_room_window_ui import Ui_AsyncRaceRoomWindow
from randovania.gui.lib import async_dialog, common_qt_lib, game_exporter
from randovania.gui.lib.background_task_mixin import BackgroundTaskMixin
from randovania.gui.lib.qt_network_client import QtNetworkClient
from randovania.gui.lib.window_manager import WindowManager
from randovania.interface_common.options import Options
from randovania.layout import preset_describer
from randovania.layout.versioned_preset import VersionedPreset
from randovania.network_common.async_race_room import (
    AsyncRaceRoomEntry,
    AsyncRaceRoomRaceStatus,
    AsyncRaceRoomUserStatus,
)


class AsyncRaceRoomWindow(QtWidgets.QMainWindow, BackgroundTaskMixin):
    CloseEvent = QtCore.Signal()

    ui: Ui_AsyncRaceRoomWindow
    room: AsyncRaceRoomEntry
    preset: VersionedPreset
    _leaderboard_dialog: AsyncRaceLeaderboardDialog | None = None

    def __init__(
        self,
        room: AsyncRaceRoomEntry,
        network_client: QtNetworkClient,
        options: Options,
        window_manager: WindowManager,
    ):
        super().__init__()
        self._network_client = network_client
        self._options = options
        self._window_manager = window_manager
        common_qt_lib.set_default_window_icon(self)

        self.ui = Ui_AsyncRaceRoomWindow()
        self.ui.setupUi(self)

        self._administration_menu = QtWidgets.QMenu(self.ui.administration_button)
        self.ui.administration_button.setMenu(self._administration_menu)
        self._administration_menu.addAction("Change options").triggered.connect(self._on_change_options)
        self._administration_menu.addAction("View user entries").triggered.connect(self._on_view_user_entries)
        self.ui.view_preset_description_button.clicked.connect(self._preset_view_summary)

        self.ui.view_spoiler_button.clicked.connect(self._view_spoiler)
        self.ui.view_leaderboard_button.clicked.connect(self._view_leaderboard)

        # TODO: background task things

        self.ui.customize_cosmetic_button.clicked.connect(self._open_user_preferences_dialog)
        self.ui.join_and_export_button.clicked.connect(self._on_join_and_export)
        self.ui.start_button.clicked.connect(self._on_start)
        self.ui.pause_button.clicked.connect(self._on_pause)
        self.ui.finish_button.clicked.connect(self._on_finish)
        self.ui.forfeit_button.clicked.connect(self._on_forfeit)
        self.ui.submit_proof_button.clicked.connect(self._on_submit_proof)
        self.on_room_details(room)

    def on_room_details(self, room: AsyncRaceRoomEntry) -> None:
        self.room = room
        now = datetime.datetime.now()

        self.ui.name_label.setText(f"Room: {room.name}")

        self.ui.start_end_date_label.setText(
            f"Race Start: {humanize.naturaltime(room.start_date, when=now)},"
            f" at {room.start_date.strftime('%c')}"
            "<br />"
            f"Race End: {humanize.naturaltime(room.end_date, when=now)},"
            f" at {room.end_date.strftime('%c')}"
        )
        presets = room.presets
        if len(presets) > 1:
            raise RuntimeError("Only single world games supported")

        self.preset = presets[0]

        game_name = self.preset.game.long_name
        self.ui.game_details_label.setText(
            f"Game: {game_name}\nHash: {room.game_details.word_hash} ({room.game_details.seed_hash})"
        )

        can_participate = room.race_status == AsyncRaceRoomRaceStatus.ACTIVE

        self.ui.customize_cosmetic_button.setEnabled(self.preset.game.gui.cosmetic_dialog is not None)
        self.ui.join_and_export_button.setEnabled(can_participate)
        self.ui.join_and_export_button.setText(
            "Join and export game" if room.self_status == AsyncRaceRoomUserStatus.NOT_MEMBER else "Re-export"
        )
        self.ui.start_button.setEnabled(
            can_participate and room.self_status in {AsyncRaceRoomUserStatus.STARTED, AsyncRaceRoomUserStatus.JOINED}
        )
        self.ui.start_button.setText("Start" if room.self_status != AsyncRaceRoomUserStatus.STARTED else "Undo Start")
        self.ui.pause_button.setVisible(room.allow_pause)
        self.ui.pause_button.setEnabled(
            can_participate and room.self_status in {AsyncRaceRoomUserStatus.STARTED, AsyncRaceRoomUserStatus.PAUSED}
        )
        self.ui.pause_button.setText("Pause" if room.self_status != AsyncRaceRoomUserStatus.PAUSED else "Unpause")
        self.ui.finish_button.setEnabled(
            can_participate and room.self_status in {AsyncRaceRoomUserStatus.STARTED, AsyncRaceRoomUserStatus.FINISHED}
        )
        self.ui.finish_button.setText(
            "Finish" if room.self_status != AsyncRaceRoomUserStatus.FINISHED else "Undo Finish"
        )
        self.ui.forfeit_button.setEnabled(
            can_participate and room.self_status in {AsyncRaceRoomUserStatus.STARTED, AsyncRaceRoomUserStatus.FORFEITED}
        )
        self.ui.forfeit_button.setText(
            "Forfeit" if room.self_status != AsyncRaceRoomUserStatus.FORFEITED else "Undo Forfeit"
        )
        self.ui.submit_proof_button.setEnabled(room.self_status == AsyncRaceRoomUserStatus.FINISHED)
        self.ui.administration_button.setEnabled(room.is_admin)

        participation_text = None
        match room.race_status:
            case AsyncRaceRoomRaceStatus.SCHEDULED:
                participation_text = f"Race starts in {humanize.naturaltime(room.start_date, when=now)}"

            case AsyncRaceRoomRaceStatus.FINISHED:
                match self.room.self_status:
                    case AsyncRaceRoomUserStatus.NOT_MEMBER:
                        extra = "You didn't join."
                    case AsyncRaceRoomUserStatus.JOINED:
                        extra = "You never started."
                    case AsyncRaceRoomUserStatus.STARTED:
                        extra = "You didn't finish."
                    case AsyncRaceRoomUserStatus.PAUSED:
                        extra = "You were paused."
                    case AsyncRaceRoomUserStatus.FINISHED:
                        extra = "You finished."
                    case AsyncRaceRoomUserStatus.FORFEITED:
                        extra = "You forfeited."
                    case _:
                        extra = f" (Unknown status {self.room.self_status.name})"
                participation_text = f"Race has finished. {extra}"

        self.ui.participation_label.setText(participation_text or "")
        self.ui.participation_label.setVisible(participation_text is not None)
        self.ui.results_group.setEnabled(room.race_status == AsyncRaceRoomRaceStatus.FINISHED)

    @asyncSlot()
    async def _preset_view_summary(self) -> None:
        preset = self.preset.get_preset()
        description = preset_describer.merge_categories(preset_describer.describe(preset))

        message_box = QtWidgets.QMessageBox(self)
        message_box.setWindowTitle(preset.name)
        message_box.setText(description)
        message_box.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        await async_dialog.execute_dialog(message_box)

    async def _status_transition(self, new_status: AsyncRaceRoomUserStatus) -> None:
        """Transitions to the requested status, and updates the UI for it."""
        self.on_room_details(await self._network_client.async_race_change_state(self.room.id, new_status))

    @asyncSlot()
    async def _on_start(self) -> None:
        """Called when the `Start` button is pressed."""
        await self._status_transition(
            AsyncRaceRoomUserStatus.STARTED
            if self.room.self_status == AsyncRaceRoomUserStatus.JOINED
            else AsyncRaceRoomUserStatus.JOINED
        )

    @asyncSlot()
    async def _on_pause(self) -> None:
        """Called when the `Pause` button is pressed."""
        await self._status_transition(
            AsyncRaceRoomUserStatus.PAUSED
            if self.room.self_status != AsyncRaceRoomUserStatus.PAUSED
            else AsyncRaceRoomUserStatus.STARTED
        )

    @asyncSlot()
    async def _on_finish(self) -> None:
        """Called when the `Finish` button is pressed."""
        await self._status_transition(
            AsyncRaceRoomUserStatus.FINISHED
            if self.room.self_status == AsyncRaceRoomUserStatus.STARTED
            else AsyncRaceRoomUserStatus.STARTED
        )

    @asyncSlot()
    async def _on_forfeit(self) -> None:
        """Called when the `Forfeit` button is pressed."""
        await self._status_transition(
            AsyncRaceRoomUserStatus.FORFEITED
            if self.room.self_status != AsyncRaceRoomUserStatus.FORFEITED
            else AsyncRaceRoomUserStatus.STARTED
        )

    @asyncSlot()
    async def _on_join_and_export(self) -> None:
        """Called when the `Join and export game` button is pressed."""
        if self.room.self_status == AsyncRaceRoomUserStatus.NOT_MEMBER and not await async_dialog.yes_no_prompt(
            self,
            "Confirm Join?",
            "After confirming this dialog and export settings, you'll enter the race.",
        ):
            return

        game = self.preset.game
        dialog = game.gui.export_dialog(
            self._options,
            self.preset.get_preset().configuration,
            self.room.game_details.word_hash,
            False,
            [game],
        )
        result = await async_dialog.execute_dialog(dialog)
        if result != QtWidgets.QDialog.DialogCode.Accepted:
            return

        patch_data = await self._network_client.async_race_join_and_export(
            self.room, self._options.generic_per_game_options(game).cosmetic_patches
        )

        dialog.save_options()
        self._can_stop_background_process = game.exporter.export_can_be_aborted
        await game_exporter.export_game(
            exporter=game.exporter,
            export_dialog=dialog,
            patch_data=patch_data,
            layout_for_spoiler=None,
            background=self,
        )
        self._can_stop_background_process = True
        await self.refresh_data()

    @asyncSlot()
    async def _open_user_preferences_dialog(self) -> None:
        await game_specific_gui.customize_cosmetic_patcher_button(
            self,
            self.preset.game,
            self._options,
            "async_race_room_window_cosmetic_clicked",
        )

    @asyncSlot()
    async def _on_submit_proof(self) -> None:
        """Called when the `Submit Proof` button is pressed."""
        dialog = AsyncRaceProofPopup(self)
        result = await async_dialog.execute_dialog(dialog)
        if result != QtWidgets.QDialog.DialogCode.Accepted:
            return

        await self._network_client.async_race_submit_proof(
            self.room.id,
            dialog.submission_notes,
            dialog.proof_url,
        )

    @asyncSlot()
    async def _view_spoiler(self) -> None:
        """Opens a GameDetailsWindow with the layout for this room"""

        try:
            self.setEnabled(False)
            layout = await self._network_client.async_race_get_layout(self.room)
        finally:
            self.setEnabled(True)

        self._window_manager.open_game_details(layout)

    @asyncSlot()
    async def _view_leaderboard(self) -> None:
        """Opens a widget with the leaderboard results"""
        if self._leaderboard_dialog is not None:
            self._leaderboard_dialog.raise_()
            return

        try:
            self.setEnabled(False)
            leaderboard = await self._network_client.async_race_get_leaderboard(self.room)
        finally:
            self.setEnabled(True)

        self._leaderboard_dialog = AsyncRaceLeaderboardDialog(self, leaderboard)
        try:
            await async_dialog.execute_dialog(self._leaderboard_dialog)
        finally:
            self._leaderboard_dialog = None

    @asyncSlot()
    async def _on_change_options(self) -> None:
        """Called when the `Change room options` button is pressed."""

        dialog = AsyncRaceSettingsDialog(self, self.room)

        result = await async_dialog.execute_dialog(dialog)
        if result == QtWidgets.QDialog.DialogCode.Accepted:
            self.on_room_details(
                await self._network_client.async_race_change_room_settings(
                    self.room.id, dialog.create_settings_object()
                )
            )

    @asyncSlot()
    async def _on_view_user_entries(self) -> None:
        data = await self._network_client.async_race_admin_get_admin_data(self.room.id)
        dialog = AsyncRaceAdminDialog(self, data)

        result = await async_dialog.execute_dialog(dialog)
        if result == QtWidgets.QDialog.DialogCode.Accepted:
            new_data = dialog.admin_data()
            modified_entries = [new for old, new in zip(data.users, new_data.users) if old != new]
            self.on_room_details(
                await self._network_client.async_race_admin_update_entries(self.room.id, modified_entries)
            )

    @asyncSlot()
    async def refresh_data(self) -> None:
        """
        Requests new room data from the server, then updates the UI.
        """
        self.on_room_details(await self._network_client.async_race_refresh_room(self.room))
