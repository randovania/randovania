from __future__ import annotations

import datetime
import logging
import typing
from typing import TYPE_CHECKING, override

import humanize
from PySide6 import QtCore, QtGui, QtWidgets
from qasync import asyncSlot

from randovania.gui import game_specific_gui
from randovania.gui.dialog.async_race.async_race_admin_dialog import AsyncRaceAdminDialog
from randovania.gui.dialog.async_race.async_race_leaderboard_dialog import AsyncRaceLeaderboardDialog
from randovania.gui.dialog.async_race.async_race_proof_popup import AsyncRaceProofPopup
from randovania.gui.dialog.async_race.async_race_settings_dialog import AsyncRaceSettingsDialog
from randovania.gui.dialog.text_prompt_dialog import TextPromptDialog
from randovania.gui.generated.async_race_room_window_ui import Ui_AsyncRaceRoomWindow
from randovania.gui.lib import async_dialog, common_qt_lib, game_exporter
from randovania.gui.lib.time_lib import format_elapsed_time
from randovania.gui.widgets.audit_log_model import AuditEntryListDatabaseModel
from randovania.layout import preset_describer
from randovania.network_common.async_race_room import (
    AsyncRaceRoomEntry,
    AsyncRaceRoomRaceStatus,
    AsyncRaceRoomUserStatus,
    AsyncRaceTeamEntry,
    AsyncRaceTeamMember,
    AsyncRaceWorldEntry,
)
from randovania.network_common.signals import server_signals

if TYPE_CHECKING:
    from randovania.gui.lib.qt_network_client import QtNetworkClient
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.options import Options
    from randovania.layout.versioned_preset import VersionedPreset


class AsyncRaceRoomWindow(QtWidgets.QMainWindow):
    CloseEvent = QtCore.Signal()

    ui: Ui_AsyncRaceRoomWindow
    room: AsyncRaceRoomEntry
    presets: list[VersionedPreset]
    _leaderboard_dialog: AsyncRaceLeaderboardDialog | None = None
    _audit_log_dialog: QtWidgets.QDialog | None = None
    _context_menu_team: AsyncRaceTeamEntry | None = None

    def __init__(
        self,
        room: AsyncRaceRoomEntry,
        network_client: QtNetworkClient,
        options: Options,
        window_manager: WindowManager,
    ) -> None:
        super().__init__()
        self._network_client = network_client
        self._options = options
        self._window_manager = window_manager
        common_qt_lib.set_default_window_icon(self)

        self.ui = Ui_AsyncRaceRoomWindow()
        self.ui.setupUi(self)

        network_client.AsyncRaceRoomUpdated.connect(self.on_data_from_server)

        self._refresh_timer = QtCore.QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.timeout.connect(self.refresh_data)

        self._update_time_labels_timer = QtCore.QTimer(self)
        self._update_time_labels_timer.timeout.connect(self._update_time_labels)

        self.ui.background_task_widget.progress_label.setVisible(False)

        self._administration_menu = QtWidgets.QMenu(self.ui.administration_button)
        self.ui.administration_button.setMenu(self._administration_menu)
        self._view_audit_log_action = self._administration_menu.addAction("View audit log")
        self._change_options_action = self._administration_menu.addAction("Change options")
        self._view_user_entries_action = self._administration_menu.addAction("View user entries")

        self.ui.view_preset_description_button.clicked.connect(self._preset_view_summary)
        self.ui.view_spoiler_button.clicked.connect(self._view_spoiler)
        self.ui.view_leaderboard_button.clicked.connect(self._view_leaderboard)
        self.ui.livesplit_button.clicked.connect(self._get_livesplit_url)
        self._view_audit_log_action.triggered.connect(self._on_view_audit_log)
        self._change_options_action.triggered.connect(self._on_change_options)
        self._view_user_entries_action.triggered.connect(self._on_view_user_entries)

        self.ui.customize_cosmetic_button.clicked.connect(self._open_user_preferences_dialog)
        self.ui.join_and_export_button.clicked.connect(self._on_join_and_export)
        self.ui.start_button.clicked.connect(self._on_start)
        self.ui.pause_button.clicked.connect(self._on_pause)
        self.ui.finish_button.clicked.connect(self._on_finish)
        self.ui.forfeit_button.clicked.connect(self._on_forfeit)
        self.ui.submit_proof_button.clicked.connect(self._on_submit_proof)

        self.ui.teams_table.setColumnCount(3)
        self.ui.teams_table.setHorizontalHeaderLabels(["Team", "Members", "Status"])
        self.ui.worlds_table.setColumnCount(3)
        self.ui.worlds_table.setHorizontalHeaderLabels(["World", "Game", "Played by"])

        for table, stretched_column in ((self.ui.teams_table, 1), (self.ui.worlds_table, 2)):
            header = table.horizontalHeader()
            for column in range(table.columnCount()):
                header.setSectionResizeMode(
                    column,
                    QtWidgets.QHeaderView.ResizeMode.Stretch
                    if column == stretched_column
                    else QtWidgets.QHeaderView.ResizeMode.ResizeToContents,
                )

        self.ui.create_team_button.clicked.connect(self._on_create_team)
        self.ui.join_team_button.clicked.connect(self._on_join_team)
        self.ui.leave_team_button.clicked.connect(self._on_leave_team)
        self.ui.team_join_code_button.clicked.connect(self._on_copy_join_code)
        self.ui.teams_table.customContextMenuRequested.connect(self._on_teams_context_menu)

        self.on_room_details(room)

    @property
    def preset(self) -> VersionedPreset:
        """
        The preset this window's buttons act on: the world selected in the worlds table, or the
        first one when nothing is selected.
        """
        return self.presets[self._selected_world_order()]

    def _selected_world_order(self) -> int:
        """The world the worlds table has selected, defaulting to the first one."""
        row = self.ui.worlds_table.currentRow()
        if 0 <= row < len(self.presets):
            return row
        return 0

    @override
    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        try:
            self._network_client.AsyncRaceRoomUpdated.disconnect(self.on_data_from_server)
        except Exception as e:
            logging.exception(f"Unable to disconnect: {e}")

        self.CloseEvent.emit()
        super().closeEvent(event)

    def on_room_details(self, room: AsyncRaceRoomEntry) -> None:
        self.room = room

        self.ui.name_label.setText(f"Room: {room.name}")
        self._update_time_labels()

        self.presets = room.presets

        if room.is_multiworld:
            games = sorted({preset.game.long_name for preset in self.presets})
            game_name = f"{', '.join(games)} ({room.world_count} worlds)"
        else:
            game_name = self.preset.game.long_name

        self.ui.game_details_label.setText(
            f"Game: {game_name}\nHash: {room.game_details.word_hash} ({room.game_details.seed_hash})"
        )

        can_participate = room.race_status == AsyncRaceRoomRaceStatus.ACTIVE
        self._update_teams_ui()
        self._update_export_button()

        can_control = can_participate and room.can_control_timer
        can_control_team = can_participate and room.can_control_team

        if room.can_control_timer:
            timer_tip = ""
        elif room.shared_team_timer:
            timer_tip = "Only the team's captain can control the timer"
        else:
            timer_tip = "Only the team's captain can start the race; after that you control your own timer"

        team_tip = "" if room.can_control_team else "Only the team's captain can start or forfeit the race"

        # Starting and forfeiting are the team's as a whole, so they follow the team's state rather
        # than what this member's own timer happens to be doing.
        own_team = room.self_team
        team_status = room.self_status if own_team is None or own_team.status is None else own_team.status

        self.ui.start_button.setEnabled(
            can_control_team and team_status in {AsyncRaceRoomUserStatus.STARTED, AsyncRaceRoomUserStatus.JOINED}
        )
        self.ui.start_button.setText("Start" if team_status != AsyncRaceRoomUserStatus.STARTED else "Undo Start")
        self.ui.pause_button.setVisible(room.allow_pause)
        self.ui.pause_button.setEnabled(
            can_control and room.self_status in {AsyncRaceRoomUserStatus.STARTED, AsyncRaceRoomUserStatus.PAUSED}
        )
        self.ui.pause_button.setText("Pause" if room.self_status != AsyncRaceRoomUserStatus.PAUSED else "Unpause")
        self.ui.finish_button.setEnabled(
            can_control and room.self_status in {AsyncRaceRoomUserStatus.STARTED, AsyncRaceRoomUserStatus.FINISHED}
        )
        self.ui.finish_button.setText(
            "Finish" if room.self_status != AsyncRaceRoomUserStatus.FINISHED else "Undo Finish"
        )
        self.ui.forfeit_button.setEnabled(
            can_control_team and team_status in {AsyncRaceRoomUserStatus.STARTED, AsyncRaceRoomUserStatus.FORFEITED}
        )
        self.ui.forfeit_button.setText(
            "Forfeit" if team_status != AsyncRaceRoomUserStatus.FORFEITED else "Undo Forfeit"
        )
        for button in (self.ui.pause_button, self.ui.finish_button):
            button.setToolTip(timer_tip)
        for button in (self.ui.start_button, self.ui.forfeit_button):
            button.setToolTip(team_tip)

        self.ui.submit_proof_button.setEnabled(room.self_status == AsyncRaceRoomUserStatus.FINISHED)
        self.ui.livesplit_button.setEnabled(
            can_control
            and room.self_status
            in {
                AsyncRaceRoomUserStatus.JOINED,
                AsyncRaceRoomUserStatus.STARTED,
                AsyncRaceRoomUserStatus.PAUSED,
                AsyncRaceRoomUserStatus.FINISHED,
            }
        )
        self.ui.livesplit_button.setToolTip(timer_tip)
        self._view_audit_log_action.setEnabled(room.is_admin)
        self._change_options_action.setEnabled(room.is_admin)
        self._view_user_entries_action.setEnabled(room.is_admin)

        self._update_participation_label()
        self.ui.results_group.setEnabled(room.race_status == AsyncRaceRoomRaceStatus.FINISHED)

        refresh_delta = None
        now = datetime.datetime.now(datetime.UTC)
        match room.race_status:
            case AsyncRaceRoomRaceStatus.SCHEDULED:
                refresh_delta = room.start_date - now

            case AsyncRaceRoomRaceStatus.ACTIVE:
                refresh_delta = room.end_date - now

        self._refresh_timer.stop()
        if refresh_delta is not None:
            timer_range = min(int(refresh_delta.total_seconds() * 1000), 15 * 60_000)
            self._refresh_timer.start(max(1000, timer_range))
            self._update_time_labels_timer.start(max(1000, timer_range // 15))

    def _update_participation_label(self) -> None:
        room = self.room
        texts = []

        if room.race_status == AsyncRaceRoomRaceStatus.FINISHED:
            match room.self_status:
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
                    extra = f" (Unknown status {room.self_status.name})"
            texts.append(f"Race has finished. {extra}")

        if room.self_time is not None:
            name = "Your team's time" if room.uses_teams else "Your time"
            texts.append(f"{name}: {format_elapsed_time(room.self_time)}")

        self.ui.participation_label.setText(" ".join(texts))
        self.ui.participation_label.setVisible(bool(texts))

    def _member_text(self, team: AsyncRaceTeamEntry, member: AsyncRaceTeamMember) -> str:
        """
        How one member of a team is listed. A team accumulating its members' times shows each
        member's own state, since they are all running separate timers, along with the time they
        contributed once they're done. Neither is known for a team other than the user's own,
        until the race is over.
        """
        text = member.user.name
        if team.captain is not None and member.user.id == team.captain.id:
            text = f"{text} (captain)"
        status = member.status
        if not self.room.shared_team_timer and status is not None and status != AsyncRaceRoomUserStatus.JOINED:
            text = f"{text} - {status.value}"
            if member.time is not None:
                text = f"{text} ({format_elapsed_time(member.time)})"
        return text

    def _played_by_text(self, world: AsyncRaceWorldEntry | None) -> str:
        """Who is playing a world. Blank when the user has no team, and so isn't told."""
        if world is None:
            return ""
        return ", ".join(user.name for user in world.claimed_by) if world.claimed_by else "(unclaimed)"

    def _update_teams_ui(self) -> None:
        """Fills in the Teams group, which only exists for rooms played in teams."""
        room = self.room
        self.ui.teams_group.setVisible(room.uses_teams)
        if not room.uses_teams:
            return

        own_team = room.self_team
        can_participate = room.race_status != AsyncRaceRoomRaceStatus.FINISHED
        before_start = room.self_status in {AsyncRaceRoomUserStatus.NOT_MEMBER, AsyncRaceRoomUserStatus.JOINED}

        worlds_text = f"{room.world_count} world multiworld" if room.is_multiworld else "shared single world"
        timer_text = (
            "The whole team shares one timer."
            if room.shared_team_timer
            else "Every member is timed separately and their times are added up."
        )
        self.ui.teams_label.setText(
            f"Teams race this {worlds_text} separately. {timer_text}"
            " The captain starts the race for the team."
            " Create a team and share its join code, or join one with a code you were given."
            " Right click your team to open its multiworld session, where you claim and export the world"
            " you'll play."
        )

        self.ui.teams_table.setRowCount(len(room.teams))
        for row, team in enumerate(room.teams):
            members = ", ".join(self._member_text(team, member) for member in team.members)
            cells = [
                team.name,
                f"{members} ({team.member_count})",
                # A rival's progress is withheld until the race is over
                team.status.value if team.status is not None else "-",
            ]
            for column, text in enumerate(cells):
                self.ui.teams_table.setItem(row, column, QtWidgets.QTableWidgetItem(text))

        own_worlds = {world.order: world for world in own_team.worlds} if own_team is not None else {}
        self.ui.worlds_table.setRowCount(len(self.presets))
        for order, preset in enumerate(self.presets):
            world = own_worlds.get(order)
            cells = [
                world.name if world is not None else f"World {order + 1}",
                preset.game.long_name,
                # More than one name here means the team is playing that world in co-op.
                self._played_by_text(world),
            ]
            for column, text in enumerate(cells):
                self.ui.worlds_table.setItem(order, column, QtWidgets.QTableWidgetItem(text))

        self.ui.create_team_button.setEnabled(can_participate and own_team is None)
        self.ui.join_team_button.setEnabled(can_participate and own_team is None)
        # Exporting means having seen part of a seed every other team also plays, so there's
        # no going back to a different team afterwards.
        self.ui.leave_team_button.setEnabled(own_team is not None and before_start and not room.self_has_exported)
        self.ui.leave_team_button.setToolTip(
            "Can't leave a team after exporting a game" if room.self_has_exported else ""
        )
        self.ui.team_join_code_button.setEnabled(own_team is not None)

    def _update_export_button(self) -> None:
        """
        Only used by single-world layout because multiworld uses the multiplayer session.
        """
        room = self.room

        self.ui.join_and_export_button.setVisible(not room.uses_teams)
        self.ui.customize_cosmetic_button.setVisible(not room.uses_teams)
        if room.uses_teams:
            return

        self.ui.join_and_export_button.setEnabled(room.race_status == AsyncRaceRoomRaceStatus.ACTIVE)
        self.ui.join_and_export_button.setText(
            "Join and export game" if room.self_status == AsyncRaceRoomUserStatus.NOT_MEMBER else "Re-export"
        )
        self.ui.customize_cosmetic_button.setEnabled(self.preset.game.gui.cosmetic_dialog is not None)

    def _update_time_labels(self) -> None:
        now = datetime.datetime.now()

        self.ui.start_end_date_label.setText(
            f"Race Start: {humanize.naturaltime(self.room.start_date, when=now)},"
            f" at {self.room.start_date.astimezone(None).strftime('%c')}"
            "<br />"
            f"Race End: {humanize.naturaltime(self.room.end_date, when=now)},"
            f" at {self.room.end_date.astimezone(None).strftime('%c')}"
        )

    @asyncSlot()
    async def _preset_view_summary(self) -> None:
        preset = self.preset.get_preset()
        description = preset_describer.merge_categories(preset_describer.describe(preset))

        message_box = QtWidgets.QMessageBox(self)

        def on_button(button: QtWidgets.QPushButton) -> None:
            if button is message_box.button(QtWidgets.QMessageBox.StandardButton.Save):
                path = common_qt_lib.prompt_user_for_preset_file(self, new_file=True)
                if path is None:
                    return

                self.preset.save_to_file(path)
                if not self._window_manager.preset_manager.is_included_preset_uuid(self.preset.uuid):
                    self._window_manager.preset_manager.add_new_preset(self.preset)

        message_box.setWindowTitle(preset.name)
        message_box.setText(description)
        message_box.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        message_box.setStandardButtons(
            QtWidgets.QMessageBox.StandardButton.Close | QtWidgets.QMessageBox.StandardButton.Save
        )
        message_box.buttonClicked.connect(on_button)
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
    async def _on_create_team(self) -> None:
        team_name = await TextPromptDialog.prompt(
            parent=self,
            title="Create team",
            description="Name for your new team:",
            is_modal=True,
            max_length=50,
        )
        if team_name is None:
            return

        self.on_room_details(await self._network_client.async_race_create_team(self.room, team_name))
        await self._on_copy_join_code()

    @asyncSlot()
    async def _on_join_team(self) -> None:
        join_code = await TextPromptDialog.prompt(
            parent=self,
            title="Join team",
            description="Paste the join code you received from a member of the team:",
            is_modal=True,
        )
        if join_code is None:
            return

        self.on_room_details(await self._network_client.async_race_join_team(self.room.id, join_code.strip()))

    @asyncSlot()
    async def _on_leave_team(self) -> None:
        if not await async_dialog.yes_no_prompt(
            self,
            "Leave team?",
            "You'll be removed from this team and release the world you claimed. Continue?",
        ):
            return

        self.on_room_details(await self._network_client.async_race_leave_team(self.room.id))

    @asyncSlot()
    async def _on_copy_join_code(self) -> None:
        try:
            self.setEnabled(False)
            join_code = await self._network_client.async_race_get_team_join_code(self.room.id)
        finally:
            self.setEnabled(True)

        common_qt_lib.set_clipboard(join_code)
        await TextPromptDialog.prompt(
            parent=self,
            title="Team join code",
            description="Send this code to the players you want on your team.",
            initial_value=join_code,
            is_modal=True,
            read_only=True,
        )

    def _on_teams_context_menu(self, pos: QtCore.QPoint) -> None:
        """
        Offers to open the multiplayer session of the team that was right clicked. Only your own
        team has one you can open, unless you're the room's creator and may check every team.
        """
        row = self.ui.teams_table.rowAt(pos.y())
        if not (0 <= row < len(self.room.teams)):
            return

        team = self.room.teams[row]
        self._context_menu_team = team

        menu = QtWidgets.QMenu(self.ui.teams_table)
        action = menu.addAction("Open multiworld session")
        action.setEnabled(team.session_id is not None)
        action.setToolTip(
            "Shows the item history, audit log and inventories of this team's multiworld."
            if team.session_id is not None
            else "You can only open the session of your own team."
        )
        action.triggered.connect(self._on_open_session)
        menu.exec(self.ui.teams_table.viewport().mapToGlobal(pos))

    @asyncSlot()
    async def _on_open_session(self) -> None:
        """
        Opens the multiplayer session backing the team picked in the context menu.
        """
        team = self._context_menu_team
        if team is None or team.session_id is None:
            return

        session_id = team.session_id
        try:
            self.setEnabled(False)
            # The room's creator is allowed to join other sessions.
            if team.id != self.room.self_team_id:
                await self._network_client.join_multiplayer_session(session_id, None)
            await self._network_client.listen_to_session(session_id, True)
            await self._window_manager.ensure_multiplayer_session_window(
                self._network_client, session_id, self._options
            )
        finally:
            self.setEnabled(True)

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

        patch_data = typing.cast(
            "dict",
            await self._network_client.async_race_join_and_export(
                self.room, self._options.generic_per_game_options(game).cosmetic_patches
            ),
        )

        dialog.save_options()
        self.ui.join_and_export_button.setEnabled(False)
        try:
            self.ui.background_task_widget.can_stop_background_process = game.exporter.export_can_be_aborted
            await game_exporter.export_game(
                exporter=game.exporter,
                export_dialog=dialog,
                patch_data=patch_data,
                layout_for_spoiler=None,
                background=self.ui.background_task_widget,
            )
            self.ui.background_task_widget.can_stop_background_process = True
        finally:
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

        try:
            self.setEnabled(False)
            submission_notes, proof_url = await self._network_client.async_race_get_own_proof(self.room.id)
        finally:
            self.setEnabled(True)

        dialog = AsyncRaceProofPopup(self)
        dialog.ui.notes_edit.setPlainText(submission_notes)
        dialog.ui.proof_edit.setText(proof_url)

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
    async def _get_livesplit_url(self) -> None:
        try:
            self.setEnabled(False)
            url = await self._network_client.async_race_get_livesplit_url(self.room)
            common_qt_lib.set_clipboard(url)

            await TextPromptDialog.prompt(
                parent=self,
                title="LiveSplit One URL",
                description="URL to add in 'Server Connection' in the Settings page of LiveSplit One.",
                initial_value=url,
                is_modal=True,
                read_only=True,
            )
        finally:
            self.setEnabled(True)

    @asyncSlot()
    async def _on_view_audit_log(self) -> None:
        """Opens a widget with the audit log."""
        if self._audit_log_dialog is not None:
            self._audit_log_dialog.raise_()
            return

        try:
            self.setEnabled(False)
            audit_log = await self._network_client.async_race_get_audit_log(self.room)
        finally:
            self.setEnabled(True)

        self._audit_log_dialog = QtWidgets.QDialog(self)
        self._audit_log_dialog.resize(625, 250)
        self._audit_log_dialog.setWindowTitle("Audit Log")
        root_layout = QtWidgets.QVBoxLayout(self._audit_log_dialog)

        table_view = QtWidgets.QTableView(self._audit_log_dialog)
        table_view.setAlternatingRowColors(True)
        audit_item_model = AuditEntryListDatabaseModel(audit_log)
        table_view.setModel(audit_item_model)
        root_layout.addWidget(table_view)
        table_view.resizeColumnsToContents()

        button_box = QtWidgets.QDialogButtonBox(self._audit_log_dialog)
        button_box.setStandardButtons(QtWidgets.QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(self._audit_log_dialog.accept)
        root_layout.addWidget(button_box)

        try:
            await async_dialog.execute_dialog(self._audit_log_dialog)
        finally:
            self._audit_log_dialog = None

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

    def on_data_from_server(self, room: AsyncRaceRoomEntry) -> None:
        if room.id == self.room.id:
            self.on_room_details(room)

    @asyncSlot()
    async def _stop_listening_room_update_events(self) -> None:
        await server_signals.AsyncRace.ListenToRoom.call_server(self._network_client)(self.room.id, False)

    async def request_room_update_events(self) -> None:
        # TODO: this does not restart the listener if we disconnect from the server
        await server_signals.AsyncRace.ListenToRoom.call_server(self._network_client)(self.room.id, True)
        self.CloseEvent.connect(self._stop_listening_room_update_events)
