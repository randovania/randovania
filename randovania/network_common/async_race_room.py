import dataclasses
import datetime
import enum
import typing

from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.game.game_enum import RandovaniaGame
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
    games: list[RandovaniaGame] | None
    has_password: bool
    creator: str
    creation_date: datetime.datetime
    start_date: datetime.datetime
    end_date: datetime.datetime
    visibility: "MultiplayerSessionVisibility"
    race_status: AsyncRaceRoomRaceStatus

    def game_summary(self) -> str:
        """Gets an human-presentable description of what games are involved in this room."""
        if self.games is None:
            return "Unknown"
        return self.games[0].long_name if len(self.games) == 1 else "Multiworld"


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


@dataclasses.dataclass
class AsyncRaceRoomAdminData(JsonDataclass):
    users: list[AsyncRaceEntryData]


class AsyncRaceRoomUserStatus(enum.Enum):
    NOT_MEMBER = "not-member"
    JOINED = "joined"
    STARTED = "started"
    PAUSED = "paused"
    FINISHED = "finished"
    FORFEITED = "forfeited"


@dataclasses.dataclass
class AsyncRaceRoomEntry(JsonDataclass):
    """
    Contains all data a client can receive about a AsyncRaceRoom.
    """

    id: int
    name: str
    creator: str
    creation_date: datetime.datetime
    start_date: datetime.datetime
    end_date: datetime.datetime
    visibility: "MultiplayerSessionVisibility"
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
