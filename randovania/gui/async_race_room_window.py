import datetime

import humanize
from PySide6 import QtWidgets
from qasync import asyncSlot

from randovania.gui import game_specific_gui
from randovania.gui.generated.async_race_room_window_ui import Ui_AsyncRaceRoomWindow
from randovania.gui.lib import async_dialog, common_qt_lib, game_exporter
from randovania.gui.lib.background_task_mixin import BackgroundTaskMixin
from randovania.gui.lib.qt_network_client import QtNetworkClient
from randovania.interface_common.options import Options
from randovania.layout import preset_describer
from randovania.layout.versioned_preset import VersionedPreset
from randovania.network_common.async_race_room import AsyncRaceRoomEntry, AsyncRaceRoomUserStatus


class AsyncRaceRoomWindow(QtWidgets.QMainWindow, BackgroundTaskMixin):
    ui: Ui_AsyncRaceRoomWindow
    room: AsyncRaceRoomEntry
    preset: VersionedPreset

    def __init__(self, room: AsyncRaceRoomEntry, network_client: QtNetworkClient, options: Options):
        super().__init__()
        self._network_client = network_client
        self._options = options
        common_qt_lib.set_default_window_icon(self)

        self.ui = Ui_AsyncRaceRoomWindow()
        self.ui.setupUi(self)

        # TODO: background task things

        self.ui.customize_cosmetic_button.clicked.connect(self._open_user_preferences_dialog)
        self.ui.join_and_export_button.clicked.connect(self._on_join_and_export)
        self.ui.start_button.clicked.connect(self._on_start)
        self.ui.finish_button.clicked.connect(self._on_finish)
        self.ui.forfeit_button.clicked.connect(self._on_forfeit)
        self.ui.submit_proof_button.clicked.connect(self._on_submit_proof)
        self.ui.change_options_button.clicked.connect(self._on_change_options)
        self.on_room_details(room)

    def on_room_details(self, room: AsyncRaceRoomEntry) -> None:
        self.room = room
        now = datetime.datetime.now()

        self.ui.name_label.setText(f"Room: {room.name}")

        self.ui.start_end_date_label.setText(
            f"Race Start: {humanize.naturaltime(room.start_date, when=now)},"
            f" at {humanize.naturaldate(room.start_date)}"
            "<br />"
            f"Race End: {humanize.naturaltime(room.end_date, when=now)},"
            f" at {humanize.naturaldate(room.end_date)}"
        )
        presets = room.presets
        if len(presets) > 1:
            raise RuntimeError("Only single world games supported")

        self.preset = presets[0]

        game_name = self.preset.game.long_name
        self.ui.game_details_label.setText(
            f"Game: {game_name}\nHash: {room.game_details.word_hash} ({room.game_details.seed_hash})"
        )

        categories = list(preset_describer.describe(self.preset.get_preset()))
        self.ui.layout_description_left_label.setText(preset_describer.merge_categories(categories[::2]))
        self.ui.layout_description_right_label.setText(preset_describer.merge_categories(categories[1::2]))
        self.ui.customize_cosmetic_button.setEnabled(self.preset.game.gui.cosmetic_dialog is not None)
        self.ui.join_and_export_button.setEnabled(room.self_status != AsyncRaceRoomUserStatus.ROOM_NOT_OPEN)
        self.ui.join_and_export_button.setText(
            "Join and export game"
            if room.self_status in {AsyncRaceRoomUserStatus.ROOM_NOT_OPEN, AsyncRaceRoomUserStatus.NOT_MEMBER}
            else "Re-export"
        )
        self.ui.start_button.setEnabled(
            room.self_status in {AsyncRaceRoomUserStatus.STARTED, AsyncRaceRoomUserStatus.JOINED}
        )
        self.ui.start_button.setText("Start" if room.self_status != AsyncRaceRoomUserStatus.STARTED else "Undo Start")
        self.ui.finish_button.setEnabled(
            room.self_status in {AsyncRaceRoomUserStatus.STARTED, AsyncRaceRoomUserStatus.FINISHED}
        )
        self.ui.finish_button.setText(
            "Finish" if room.self_status != AsyncRaceRoomUserStatus.FINISHED else "Undo Finish"
        )
        self.ui.forfeit_button.setEnabled(
            room.self_status in {AsyncRaceRoomUserStatus.STARTED, AsyncRaceRoomUserStatus.FORFEITED}
        )
        self.ui.forfeit_button.setText(
            "Forfeit" if room.self_status != AsyncRaceRoomUserStatus.FORFEITED else "Undo Forfeit"
        )

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
        if not await async_dialog.yes_no_prompt(
            self,
            "Confirm Join?",
            "After confirming this dialog and export settings, "
            "you have a X minutes grace period until you automatically Start.",
        ):
            return

        game = self.preset.game
        dialog = game.gui.export_dialog(
            self._options,
            {},
            self.room.game_details.word_hash,
            False,
            [game],
        )
        result = await async_dialog.execute_dialog(dialog)
        if result != QtWidgets.QDialog.DialogCode.Accepted:
            return

        patch_data = await self._network_client.async_race_join_and_export(
            self.room.id, self._options.options_for_game(game).cosmetic_patches
        )

        dialog.save_options()
        self._can_stop_background_process = game.exporter.export_can_be_aborted
        await game_exporter.export_game(
            exporter=game.exporter,
            export_dialog=dialog,
            patch_data=patch_data,
            layout_for_spoiler=None,
            background=self,
            progress_update_signal=self.progress_update_signal,
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

    @asyncSlot()
    async def _on_change_options(self) -> None:
        """Called when the `Change room options` button is pressed."""

    @asyncSlot()
    async def refresh_data(self) -> None:
        """
        Requests new room data from the server, then updates the UI.
        """
        self.on_room_details(await self._network_client.get_async_race_room(self.room.id))
