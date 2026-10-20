import base64
import datetime
import enum
import uuid
from typing import Self

from pydantic import AwareDatetime, Field, field_serializer

from randovania.game.game_enum import RandovaniaGame
from randovania.layout.versioned_preset import VersionedPreset
from randovania.lib.json_base_model import JsonBaseModel
from randovania.network_common.game_details import GameDetails
from randovania.network_common.session_visibility import MultiplayerSessionVisibility
from randovania.network_common.user import RandovaniaUser


def race_uses_teams(world_count: int, allow_coop: bool) -> bool:
    """
    Whether a race with these settings is played in teams, each hosted in its own multiplayer
    session, rather than by individual users.
    """
    return world_count > 1 or allow_coop


class AsyncRaceSettings(JsonBaseModel):
    name: str
    password: str | None
    start_date: AwareDatetime
    end_date: AwareDatetime
    visibility: MultiplayerSessionVisibility
    allow_pause: bool
    allow_coop: bool = False
    allow_abandon_worlds: bool = False
    shared_team_timer: bool = True


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
    One row of a race's results. A room played individually has one row per user, named after
    them; a room played in teams has one row per team, named after it. None for time indicates
    the participant forfeited.
    """

    display_name: str
    time: datetime.timedelta | None
    members: list[RandovaniaUser] = Field(default_factory=list)


class RaceRoomLeaderboard(JsonBaseModel):
    entries: list[RaceRoomLeaderboardEntry]
    uses_teams: bool = False


class AsyncRacePauseEntry(JsonBaseModel):
    """
    A pause attempt. End being None indicates the pause is still active.
    """

    start: datetime.datetime
    end: datetime.datetime | None


class AsyncRaceEntryData(JsonBaseModel):
    """
    All data about one participant of a race: a single user in a room played individually,
    or a whole team in a room played in teams. Should only be available to admins.
    """

    user: RandovaniaUser | None
    join_date: datetime.datetime
    start_date: datetime.datetime | None
    finish_date: datetime.datetime | None
    forfeit: bool
    pauses: list[AsyncRacePauseEntry]
    submission_notes: str
    proof_url: str
    team_id: int | None = None
    team_name: str | None = None
    members: list[RandovaniaUser] = Field(default_factory=list)

    @property
    def display_name(self) -> str:
        """How this participant is named in admin views."""
        if self.team_name is not None:
            return self.team_name
        if self.user is not None:
            return self.user.name
        return "<unknown>"

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


class AsyncRaceWorldEntry(JsonBaseModel):
    """One world of a team's multiworld, and who on the team is playing it."""

    world_uuid: uuid.UUID
    order: int
    name: str
    claimed_by: list[RandovaniaUser]

    def is_claimed_by(self, user_id: int) -> bool:
        return any(user.id == user_id for user in self.claimed_by)


class AsyncRaceTeamMember(JsonBaseModel):
    """
    One member of a team. `status` and `time` are only filled in for the user's own team, until
    the race is over; `time` also needs a team timed per member, and that member to be done.
    """

    user: RandovaniaUser
    status: AsyncRaceRoomUserStatus | None = None
    time: datetime.timedelta | None = None


class AsyncRaceTeamEntry(JsonBaseModel):
    """
    A team playing a race room. Who is on it is public; `status` is only filled in for the user's
    own team, until the race is over, and `worlds`/`session_id` for their team and the creator.
    """

    id: int
    name: str
    status: AsyncRaceRoomUserStatus | None
    members: list[AsyncRaceTeamMember]
    worlds: list[AsyncRaceWorldEntry]
    captain: RandovaniaUser | None = None
    session_id: int | None = None  # The hidden multiplayer session hosting this team's multiworld

    @property
    def member_count(self) -> int:
        return len(self.members)

    @property
    def member_users(self) -> list[RandovaniaUser]:
        return [member.user for member in self.members]

    def member_for(self, user_id: int) -> AsyncRaceTeamMember | None:
        for member in self.members:
            if member.user.id == user_id:
                return member
        return None

    def worlds_for(self, user_id: int) -> list[AsyncRaceWorldEntry]:
        """The worlds of this team the given user claimed."""
        return [world for world in self.worlds if world.is_claimed_by(user_id)]

    @property
    def unclaimed_worlds(self) -> list[AsyncRaceWorldEntry]:
        return [world for world in self.worlds if not world.claimed_by]


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
    world_count: int = 1
    self_time: datetime.timedelta | None = None
    teams: list[AsyncRaceTeamEntry] = Field(default_factory=list)
    self_team_id: int | None = None
    self_has_exported: bool = False
    self_is_captain: bool = False
    allow_coop: bool = False
    allow_abandon_worlds: bool = False
    shared_team_timer: bool = True

    @property
    def presets(self) -> list[VersionedPreset]:
        return [VersionedPreset.from_bytes(s) for s in self.presets_raw]

    @field_serializer("presets_raw")
    def serialize_presets(self, value: list[bytes]) -> list[str]:
        return [base64.b64encode(v).decode("ascii") for v in value]

    @property
    def is_multiworld(self) -> bool:
        """Whether the layout being raced has more than one world."""
        return self.world_count > 1

    @property
    def uses_teams(self) -> bool:
        """
        Rooms played in teams go through a multiplayer session; rooms without teams are played
        by individual users.
        """
        return race_uses_teams(self.world_count, self.allow_coop)

    @property
    def self_team(self) -> AsyncRaceTeamEntry | None:
        if self.self_team_id is None:
            return None
        for team in self.teams:
            if team.id == self.self_team_id:
                return team
        return None

    @property
    def can_control_team(self) -> bool:
        return not self.uses_teams or self.self_is_captain

    @property
    def can_control_timer(self) -> bool:
        if not self.uses_teams:
            return True
        if self.self_is_captain:
            return True
        if self.shared_team_timer:
            return False
        # Individual timers only become the member's own once the captain has started the race.
        return self.self_status != AsyncRaceRoomUserStatus.JOINED
