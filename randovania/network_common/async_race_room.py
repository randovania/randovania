import base64
import datetime
import enum
from typing import Self

from pydantic import AwareDatetime, field_serializer

from randovania.game.game_enum import RandovaniaGame
from randovania.layout.versioned_preset import VersionedPreset
from randovania.lib.json_base_model import JsonBaseModel
from randovania.network_common.game_details import GameDetails
from randovania.network_common.session_visibility import MultiplayerSessionVisibility
from randovania.network_common.user import RandovaniaUser


class AsyncRaceSettings(JsonBaseModel):
    name: str
    password: str | None
    start_date: AwareDatetime
    end_date: AwareDatetime
    visibility: MultiplayerSessionVisibility
    allow_pause: bool


class AsyncRaceRoomRaceStatus(enum.Enum):
    """
    Indicates if the race has already started and/or finished.
    """

    SCHEDULED = "scheduled"
    ACTIVE = "active"
    FINISHED = "finished"

    @classmethod
    def from_dates(cls, start: datetime.datetime, end: datetime.datetime, now: datetime.datetime) -> Self:
        """Calculates the status based on the given start and end dates, compared to a given now."""
        if now < start:
            return cls.SCHEDULED
        if now > end:
            return cls.FINISHED
        assert start < end
        return cls.ACTIVE


class AsyncRaceRoomListEntry(JsonBaseModel):
    """
    Contains necessary data to describe AsyncRaceRoom for a room browser.
    """

    id: int
    name: str
    games: list[RandovaniaGame] | None
    has_password: bool
    creator: str
    creation_date: datetime.datetime
    start_date: datetime.datetime
    end_date: datetime.datetime
    visibility: MultiplayerSessionVisibility
    race_status: AsyncRaceRoomRaceStatus

    def game_summary(self) -> str:
        """Gets a human-presentable description of what games are involved in this room."""
        if self.games is None:
            return "Unknown"
        return self.games[0].long_name if len(self.games) == 1 else "Multiworld"


class RaceRoomLeaderboardEntry(JsonBaseModel):
    """
    None for time indicates the user forfeited.
    """

    user: RandovaniaUser
    time: datetime.timedelta | None


class RaceRoomLeaderboard(JsonBaseModel):
    entries: list[RaceRoomLeaderboardEntry]


class AsyncRacePauseEntry(JsonBaseModel):
    """
    A pause attempt. End being None indicates the pause is still active.
    """

    start: datetime.datetime
    end: datetime.datetime | None


class AsyncRaceEntryData(JsonBaseModel):
    """
    All data about a user's entry to a race. Should only be available to admins.
    """

    user: RandovaniaUser
    join_date: datetime.datetime
    start_date: datetime.datetime | None
    finish_date: datetime.datetime | None
    forfeit: bool
    pauses: list[AsyncRacePauseEntry]
    submission_notes: str
    proof_url: str

    def is_valid(self) -> bool:
        """Returns True if all three dates are consistent, False otherwise."""
        if self.start_date is None:
            return self.finish_date is None
        else:
            if self.finish_date is not None:
                return self.join_date < self.start_date < self.finish_date
            else:
                return self.join_date < self.start_date


class AsyncRaceRoomAdminData(JsonBaseModel):
    # FIXME: The field name is weird
    users: list[AsyncRaceEntryData]


class AsyncRaceRoomUserStatus(enum.Enum):
    NOT_MEMBER = "not-member"
    JOINED = "joined"
    STARTED = "started"
    PAUSED = "paused"
    FINISHED = "finished"
    FORFEITED = "forfeited"


class AsyncRaceRoomEntry(JsonBaseModel):
    """
    Contains all data a client can receive about an AsyncRaceRoom.
    """

    id: int
    name: str
    creator: str
    creation_date: datetime.datetime
    start_date: datetime.datetime
    end_date: datetime.datetime
    visibility: MultiplayerSessionVisibility
    race_status: AsyncRaceRoomRaceStatus
    auth_token: str
    game_details: GameDetails
    presets_raw: list[bytes]
    is_admin: bool
    self_status: AsyncRaceRoomUserStatus
    allow_pause: bool

    @property
    def presets(self) -> list[VersionedPreset]:
        return [VersionedPreset.from_bytes(s) for s in self.presets_raw]

    @field_serializer("presets_raw")
    def serialize_presets(self, value: list[bytes]) -> list[str]:
        return [base64.b64encode(v).decode("ascii") for v in value]
