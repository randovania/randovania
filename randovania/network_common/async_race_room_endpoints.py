from __future__ import annotations

import dataclasses


@dataclasses.dataclass(frozen=True)
class AsyncRaceRoomEndpoints:
    prefix: str = "/async-race-room"

    list_rooms_template: str = ""
    create_room_template: str = ""
    change_room_template: str = "/{room_id}"
    get_room_template: str = "/{room_id}"
    refresh_room_template: str = "/{room_id}/refresh"
    room_leaderboard_template: str = "/{room_id}/leaderboard"
    room_layout_template: str = "/{room_id}/layout"
    room_audit_log_template: str = "/{room_id}/audit-log"
    room_admin_data_template: str = "/{room_id}/admin-data"
    room_admin_entries_template: str = "/{room_id}/admin-entries"
    room_join_and_export_template: str = "/{room_id}/join-and-export"
    room_state_template: str = "/{room_id}/state"
    room_own_proof_template: str = "/{room_id}/own-proof"
    room_submit_proof_template: str = "/{room_id}/proof"
    room_livesplit_url_template: str = "/{room_id}/livesplit-url"
    room_livesplit_integratione: str = "/{room_id}/livesplit/{token}"

    def _build(self, template: str, **kwargs: object) -> str:
        return f"{self.prefix}{template}".format(**kwargs).lstrip("/")

    def list_rooms(self) -> str:
        return self._build(self.list_rooms_template)

    def create_room(self) -> str:
        return self._build(self.create_room_template)

    def change_room(self, room_id: int) -> str:
        return self._build(self.change_room_template, room_id=room_id)

    def get_room(self, room_id: int) -> str:
        return self._build(self.get_room_template, room_id=room_id)

    def refresh_room(self, room_id: int) -> str:
        return self._build(self.refresh_room_template, room_id=room_id)

    def room_leaderboard(self, room_id: int) -> str:
        return self._build(self.room_leaderboard_template, room_id=room_id)

    def room_layout(self, room_id: int) -> str:
        return self._build(self.room_layout_template, room_id=room_id)

    def room_audit_log(self, room_id: int) -> str:
        return self._build(self.room_audit_log_template, room_id=room_id)

    def room_admin_data(self, room_id: int) -> str:
        return self._build(self.room_admin_data_template, room_id=room_id)

    def room_admin_entries(self, room_id: int) -> str:
        return self._build(self.room_admin_entries_template, room_id=room_id)

    def room_join_and_export(self, room_id: int) -> str:
        return self._build(self.room_join_and_export_template, room_id=room_id)

    def room_state(self, room_id: int) -> str:
        return self._build(self.room_state_template, room_id=room_id)

    def room_own_proof(self, room_id: int) -> str:
        return self._build(self.room_own_proof_template, room_id=room_id)

    def room_submit_proof(self, room_id: int) -> str:
        return self._build(self.room_submit_proof_template, room_id=room_id)

    def room_livesplit_url(self, room_id: int) -> str:
        return self._build(self.room_livesplit_url_template, room_id=room_id)


async_race_room_endpoints = AsyncRaceRoomEndpoints()
