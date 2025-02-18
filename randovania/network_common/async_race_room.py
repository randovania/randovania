import dataclasses
import datetime
import enum
import typing

from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.layout.versioned_preset import VersionedPreset
from randovania.network_common.game_details import GameDetails
from randovania.network_common.session_visibility import MultiplayerSessionVisibility
from randovania.network_common.user import RandovaniaUser


@dataclasses.dataclass
class AsyncRaceSettings(JsonDataclass):
    name: str
    password: str | None
    start_date: datetime.datetime
    end_date: datetime.datetime
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
    def from_dates(cls, start: datetime.datetime, end: datetime.datetime, now: datetime.datetime) -> typing.Self:
        """Calculates the status based on the given start and end dates, compared to a given now."""
        if now < start:
            return cls.SCHEDULED
        if now > end:
            return cls.FINISHED
        assert start < end
        return cls.ACTIVE


@dataclasses.dataclass
class AsyncRaceRoomListEntry(JsonDataclass):
    """
    Contains necessary data to describe AsyncRaceRoom for a room browser.
    """

    id: int
    name: str
    has_password: bool
    creator: str
    creation_date: datetime.datetime
    start_date: datetime.datetime
    end_date: datetime.datetime
    visibility: MultiplayerSessionVisibility
    race_status: AsyncRaceRoomRaceStatus


@dataclasses.dataclass
class RaceRoomLeaderboardEntry(JsonDataclass):
    """
    None for time indicates the user forfeited.
    """

    user: RandovaniaUser
    time: datetime.timedelta | None


@dataclasses.dataclass
class RaceRoomLeaderboard(JsonDataclass):
    entries: list[RaceRoomLeaderboardEntry]


@dataclasses.dataclass
class AsyncRacePauseEntry(JsonDataclass):
    """
    A pause attempt. End being None indicates the pause is still active.
    """

    start: datetime.datetime
    end: datetime.datetime | None


@dataclasses.dataclass
class AsyncRaceEntryData(JsonDataclass):
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
    proof_url: str | None


@dataclasses.dataclass
class AsyncRaceRoomAdminData(JsonDataclass):
    users: list[AsyncRaceEntryData]


class AsyncRaceRoomUserStatus(enum.Enum):
    ROOM_NOT_OPEN = "room-not-open"
    NOT_MEMBER = "not-member"
    JOINED = "joined"
    STARTED = "started"
    PAUSED = "paused"
    FINISHED = "finished"
    FORFEITED = "forfeited"


@dataclasses.dataclass
class AsyncRaceRoomEntry(AsyncRaceRoomListEntry):
    """
    Contains all data a client can receive about a AsyncRaceRoom.
    """

    game_details: GameDetails
    presets_raw: list[bytes]
    is_admin: bool
    self_status: AsyncRaceRoomUserStatus
    allow_pause: bool
    leaderboard: RaceRoomLeaderboard | None

    @property
    def presets(self) -> list[VersionedPreset]:
        return [VersionedPreset.from_bytes(s) for s in self.presets_raw]
