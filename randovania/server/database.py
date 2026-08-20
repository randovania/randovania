# mypy: disable-error-code="assignment"

from __future__ import annotations

import collections
import datetime
import enum
import json
import typing
import uuid
import zlib
from contextlib import asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any, Self
from uuid import UUID

import cachetools
import peewee
from sentry_sdk.tracing_utils import record_sql_queries

from randovania.game.game_enum import RandovaniaGame
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.layout.layout_description import LayoutDescription
from randovania.layout.versioned_preset import VersionedPreset
from randovania.lib import pydantic_util
from randovania.network_common import async_race_room, error, multiplayer_session
from randovania.network_common.async_race_room import AsyncRaceRoomRaceStatus
from randovania.network_common.audit import AuditEntry
from randovania.network_common.discord_preferences import GuildPreferences
from randovania.network_common.game_connection_status import GameConnectionStatus
from randovania.network_common.game_details import GameDetails
from randovania.network_common.multiplayer_session import (
    MAX_SESSION_NAME_LENGTH,
    MAX_WORLD_NAME_LENGTH,
    MultiplayerSessionAuditLog,
    MultiplayerUser,
    MultiplayerWorld,
    UserWorldDetail,
)
from randovania.network_common.session_visibility import MultiplayerSessionVisibility
from randovania.network_common.user import RandovaniaUser
from randovania.server import lib

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Sequence

    from randovania.lib.json_lib import JsonObject
    from randovania.server.server_app import Lifespan, RdvFastAPI, ServerApp

    class TypedModelSelect[T](typing.Protocol):
        def where(self, *expressions: Any) -> Self: ...

        def limit(self, value: Any) -> Self: ...

        def order_by(self, *values: Any) -> Self: ...

        def join(self, dest: Any, join_type: Any = None, on: Any = None) -> Any: ...

        def count(self, clear_limit: bool = False) -> int: ...

        def __iter__(self) -> Iterator[T]: ...

        def paginate(self, page_number: int, items_per_page: int) -> Self: ...


class MonitoredDb(peewee.SqliteDatabase):
    def execute_sql(self, sql, params=None, commit=peewee.SENTINEL):  # type: ignore[no-untyped-def]
        with record_sql_queries(self.cursor, sql, params, paramstyle="format", executemany=False):
            return super().execute_sql(sql, params, commit)


db = MonitoredDb(None, pragmas={"foreign_keys": 1}, autoconnect=False)


def is_boolean(field: Any, value: bool) -> bool:
    return field == value


class BaseModel(peewee.Model):
    DoesNotExist: type[peewee.DoesNotExist]

    class Meta:
        database = db
        legacy_table_names = False

    @classmethod
    def create(cls, **query: Any) -> Self:
        return super().create(**query)

    @classmethod
    def get(cls, *query: Any, **filters: Any) -> Self:
        return super().get(*query, **filters)

    @classmethod
    def get_by_id(cls, pk: int) -> Self:
        return super().get_by_id(pk)

    @classmethod
    def get_or_create(cls, **kwargs: Any) -> tuple[Self, bool]:
        return super().get_or_create(**kwargs)

    @classmethod
    def select(cls, *fields: Any) -> TypedModelSelect[Self]:
        return super().select(*fields)


class EnumField(peewee.CharField):
    """
    This class enable an Enum like field for Peewee
    """

    def __init__(self, choices: type[enum.Enum], *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.choices = choices
        self.max_length = 255

    def db_value(self, value: Any) -> Any:
        return value.value

    def python_value(self, value: Any) -> Any:
        return self.choices(type(next(iter(self.choices)).value)(value))


class User(BaseModel):
    id: int
    discord_id: int | None = peewee.IntegerField(index=True, null=True)
    name: str = peewee.CharField()
    admin: bool = peewee.BooleanField(default=False)
    access_tokens: Iterable[UserAccessToken]

    @property
    def as_json(self) -> JsonObject:
        return {
            "id": self.id,
            "name": self.name,
            "discord_id": self.discord_id,
        }

    def as_randovania_user(self) -> RandovaniaUser:
        return RandovaniaUser(id=self.id, name=self.name)


class UserAccessToken(BaseModel):
    user = peewee.ForeignKeyField(User, backref="access_tokens")
    name = peewee.CharField()
    creation_date = peewee.DateTimeField(default=lib.datetime_now)
    last_used: datetime.datetime = peewee.DateTimeField(default=lib.datetime_now)

    class Meta:
        primary_key = peewee.CompositeKey("user", "name")

    @property
    def creation_datetime(self) -> datetime.datetime:
        return datetime.datetime.fromisoformat(self.creation_date)  # type: ignore[arg-type]

    @property
    def last_used_datetime(self) -> datetime.datetime:
        return datetime.datetime.fromisoformat(self.creation_date)  # type: ignore[arg-type]


@cachetools.cached(cache=cachetools.TTLCache(maxsize=64, ttl=600))
def _decode_layout_description(layout: bytes, presets: tuple[str, ...]) -> LayoutDescription:
    preset_list: list[VersionedPreset] = [VersionedPreset.from_str(preset) for preset in presets]
    if layout.startswith(b"RDVG"):
        return LayoutDescription.from_bytes(layout, presets=preset_list)
    else:
        # If the file doesn't have our prefix, it's from before it used BinaryLayoutDescription
        decoded = json.loads(zlib.decompress(layout).decode("utf-8"))
        decoded["info"]["presets"] = [preset.as_json for preset in preset_list]
        return LayoutDescription.from_json_dict(decoded)


class MultiplayerSession(BaseModel):
    id: int
    name: str = peewee.CharField(max_length=MAX_SESSION_NAME_LENGTH)
    password: str | None = peewee.CharField(null=True)
    visibility: MultiplayerSessionVisibility = EnumField(
        choices=MultiplayerSessionVisibility, default=MultiplayerSessionVisibility.VISIBLE
    )
    layout_description_json: bytes | None = peewee.BlobField(null=True)
    game_details_json: str | None = peewee.CharField(null=True)
    creator: User = peewee.ForeignKeyField(User)
    creation_date: str = peewee.DateTimeField(default=lib.datetime_now)
    generation_in_progress: User | None = peewee.ForeignKeyField(User, null=True)
    dev_features: str | None = peewee.CharField(null=True)

    allow_coop: bool = peewee.BooleanField(default=False)
    allow_everyone_claim_world: bool = peewee.BooleanField(default=False)
    allow_abandon_worlds: bool = peewee.BooleanField(default=True)

    race_team = peewee.DeferredForeignKey("AsyncRaceTeam", null=True, backref="sessions", unique=True)
    race_team_id: int | None

    members: list[MultiplayerMembership]
    worlds: list[World]
    audit_log: list[MultiplayerAuditEntry]

    def has_layout_description(self) -> bool:
        return self.layout_description_json is not None

    @property
    def is_race_session(self) -> bool:
        return self.race_team_id is not None

    def get_race_team(self) -> AsyncRaceTeam | None:
        return typing.cast("AsyncRaceTeam | None", self.race_team)

    def _get_layout_description(self, ordered_worlds: list[World]) -> LayoutDescription:
        assert self.layout_description_json is not None
        return _decode_layout_description(self.layout_description_json, tuple(world.preset for world in ordered_worlds))

    @property
    def layout_description(self) -> LayoutDescription | None:
        if self.layout_description_json is not None:
            return self._get_layout_description(self.get_ordered_worlds())
        else:
            return None

    @layout_description.setter
    def layout_description(self, description: LayoutDescription | None) -> None:
        if description is not None:
            encoded = description.as_binary(force_spoiler=True, include_presets=False)
            self.layout_description_json = encoded
            self.game_details_json = json.dumps(
                GameDetails(
                    spoiler=description.has_spoiler,
                    word_hash=description.shareable_word_hash,
                    seed_hash=description.shareable_hash,
                ).as_json
            )
        else:
            self.layout_description_json = None
            self.game_details_json = None

    def get_layout_description_as_json(self) -> dict | None:
        """Get the stored LayoutDescription as a JSON object"""
        if self.layout_description_json is not None:
            return LayoutDescription.bytes_to_dict(
                self.layout_description_json,
                presets=[VersionedPreset.from_str(world.preset) for world in self.get_ordered_worlds()],
            )
        return None

    def get_layout_description_as_binary(self) -> bytes | None:
        layout = self.layout_description
        if layout is not None:
            # TODO: just return layout_description_json directly!
            return layout.as_binary(include_presets=False, force_spoiler=True)
        else:
            return None

    def game_details(self) -> GameDetails | None:
        if self.game_details_json is not None:
            return GameDetails.from_json(json.loads(self.game_details_json))
        return None

    @property
    def creation_datetime(self) -> datetime.datetime:
        return datetime.datetime.fromisoformat(self.creation_date)

    def is_user_in_session(self, user: User) -> bool:
        try:
            MultiplayerMembership.get_by_ids(user, self.id)
        except peewee.DoesNotExist:
            return False
        return True

    @property
    def allowed_games(self) -> list[RandovaniaGame]:
        dev_features = self.dev_features or ""
        return [
            game
            for game in RandovaniaGame.sorted_all_games()
            if game.data.defaults_available_in_game_sessions or game.value in dev_features
        ]

    def get_ordered_worlds(self) -> list[World]:
        return list(World.select().where(World.session == self).order_by(World.order.asc()))  # type: ignore[union-attr]

    def describe_actions(self, last_count: int = 1000) -> multiplayer_session.MultiplayerSessionActions:
        if not self.has_layout_description():
            return multiplayer_session.MultiplayerSessionActions(self.id, [])

        worlds = self.get_ordered_worlds()
        description: LayoutDescription = self._get_layout_description(worlds)
        world_by_id = {world.get_id(): world for world in worlds}

        def _describe_action(action: WorldAction) -> multiplayer_session.MultiplayerSessionAction:
            provider = world_by_id[action.provider_id]
            receiver = world_by_id[action.receiver_id]

            assert provider.order is not None

            location_index = PickupIndex(action.location)
            target = description.all_patches[provider.order].pickup_assignment.get(location_index, None)

            return multiplayer_session.MultiplayerSessionAction(
                provider=provider.uuid,
                receiver=receiver.uuid,
                pickup=target.pickup.name if target else "Nothing",
                location=action.location,
                time=datetime.datetime.fromisoformat(action.time),
            )

        return multiplayer_session.MultiplayerSessionActions(
            self.id,
            list(
                reversed(
                    [
                        _describe_action(action)
                        for action in WorldAction.select()
                        .where(
                            WorldAction.session == self,
                        )
                        .order_by(
                            WorldAction.time.desc(),  # type: ignore[attr-defined]
                        )
                        .limit(
                            last_count,
                        )
                    ]
                )
            ),
        )

    def create_session_entry(self) -> multiplayer_session.MultiplayerSessionEntry:
        game_details = None
        if self.game_details_json is not None:
            game_details = GameDetails.from_json(json.loads(self.game_details_json))

        # Get the worlds explicitly, as we return them and would also need for the user assocations
        worlds = {
            world.id: MultiplayerWorld(
                id=world.uuid,
                name=world.name,
                preset_raw=world.preset,
                has_been_beaten=world.beaten,
                is_abandoned=world.abandoned,
            )
            for world in self.worlds
        }

        # Fetch the members, with a Join to also fetch the member name
        members: Iterable[MultiplayerMembership] = (
            MultiplayerMembership.select(
                MultiplayerMembership.admin,
                MultiplayerMembership.ready,
                User.id,
                User.name,
            )
            .join(User)
            .where(
                MultiplayerMembership.session == self.id,
            )
        )

        # Fetch all user associations up-front, then split per user
        associations: Iterable[WorldUserAssociation] = (
            WorldUserAssociation.select(
                WorldUserAssociation.user,
                WorldUserAssociation.world,
                WorldUserAssociation.connection_state,
                WorldUserAssociation.last_activity,
            )
            .join(World)
            .where(
                World.session == self.id,
            )
        )

        association_by_user: dict[int, list[WorldUserAssociation]] = collections.defaultdict(list)
        for association in associations:
            association_by_user[association.user_id].append(association)

        return multiplayer_session.MultiplayerSessionEntry(
            id=self.id,
            name=self.name,
            visibility=self.visibility,
            users_list=[
                MultiplayerUser(
                    id=member.user_id,
                    name=member.user.name,
                    admin=member.admin,
                    ready=member.ready,
                    worlds={
                        worlds[association.world_id].id: UserWorldDetail(
                            connection_state=association.connection_state,
                            last_activity=association.last_activity,
                        )
                        for association in association_by_user[member.user_id]
                    },
                )
                for member in members
            ],
            worlds=list(worlds.values()),
            game_details=game_details,
            generation_in_progress=(
                self.generation_in_progress.id if self.generation_in_progress is not None else None
            ),
            allowed_games=self.allowed_games,
            allow_coop=self.allow_coop,
            allow_everyone_claim_world=self.allow_everyone_claim_world,
            allow_abandon_worlds=self.allow_abandon_worlds,
            is_race_session=self.is_race_session,
        )

    def get_audit_log(self) -> MultiplayerSessionAuditLog:
        audit_log = (
            MultiplayerAuditEntry.select(MultiplayerAuditEntry, User.name)
            .join(User)
            .where(MultiplayerAuditEntry.session == self)
        )

        return MultiplayerSessionAuditLog(session_id=self.id, entries=[entry.as_entry() for entry in audit_log])


class World(BaseModel):
    id: int
    session: MultiplayerSession = peewee.ForeignKeyField(MultiplayerSession, backref="worlds")
    session_id: int
    uuid: UUID = peewee.UUIDField(default=uuid.uuid4, unique=True)

    name: str = peewee.CharField(max_length=MAX_WORLD_NAME_LENGTH)
    preset: str = peewee.TextField()
    order: int | None = peewee.IntegerField(null=True, default=None)
    beaten: bool = peewee.BooleanField(default=False)
    abandoned: bool = peewee.BooleanField(default=False)

    associations: list[WorldUserAssociation]

    @classmethod
    def get_by_uuid(cls, uid: UUID | str) -> World:
        try:
            return cls.get(World.uuid == uid)
        except peewee.DoesNotExist:
            raise error.WorldDoesNotExistError

    @classmethod
    def get_by_order(cls, session_id: int, order: int) -> World:
        return cls.get(
            World.session == session_id,
            World.order == order,
        )

    @classmethod
    def create_for(
        cls,
        session: MultiplayerSession,
        name: str,
        preset: VersionedPreset,
        *,
        uid: UUID | None = None,
        order: int | None = None,
        beaten: bool = False,
        abandoned: bool = False,
    ) -> Self:
        if uid is None:
            uid = uuid.uuid4()
        return cls().create(
            session=session,
            uuid=uid,
            name=name,
            preset=json.dumps(preset.as_json, separators=(",", ":")),
            order=order,
            beaten=beaten,
            abandoned=abandoned,
        )


class WorldUserAssociation(BaseModel):
    """A given user's association to one given row."""

    world: World = peewee.ForeignKeyField(World, backref="associations")
    world_id: int
    user: User = peewee.ForeignKeyField(User)
    user_id: int

    connection_state: GameConnectionStatus = EnumField(
        choices=GameConnectionStatus, default=GameConnectionStatus.Disconnected
    )
    last_activity: datetime.datetime = peewee.DateTimeField(default=lib.datetime_now)
    inventory: bytes = peewee.BlobField(null=True)

    @classmethod
    def get_by_instances(cls, *, world: World | int, user: User | int) -> Self:
        return cls.get(
            WorldUserAssociation.world == world,
            WorldUserAssociation.user == user,
        )

    @classmethod
    def get_by_ids(cls, world_uid: UUID, user_id: int) -> Self:
        return (
            cls.select()
            .join(World)
            .where(
                World.uuid == world_uid,
                WorldUserAssociation.user == user_id,
            )
            .get()
        )

    @classmethod
    def find_all_for_user_in_session(cls, user_id: int, session_id: int) -> Iterable[Self]:
        yield from (
            cls.select()
            .join(World)
            .where(
                World.session == session_id,
                WorldUserAssociation.user == user_id,
            )
        )

    class Meta:
        primary_key = peewee.CompositeKey("world", "user")
        only_save_dirty = True


class MultiplayerMembership(BaseModel):
    user: User = peewee.ForeignKeyField(User, backref="sessions")
    user_id: int
    session: MultiplayerSession = peewee.ForeignKeyField(MultiplayerSession, backref="members")
    session_id: int
    admin: bool = peewee.BooleanField(default=False)
    ready: bool = peewee.BooleanField(default=False)
    join_date = peewee.DateTimeField(default=lib.datetime_now)

    can_help_layout_generation: bool = peewee.BooleanField(default=False)

    @property
    def effective_name(self) -> str:
        return self.user.name

    @classmethod
    def get_by_ids(cls, user_id: int | User, session_id: int | MultiplayerSession) -> Self:
        return cls.get(
            MultiplayerMembership.session == session_id,
            MultiplayerMembership.user == user_id,
        )

    class Meta:
        primary_key = peewee.CompositeKey("user", "session")


class WorldAction(BaseModel):
    provider: World = peewee.ForeignKeyField(World, backref="actions")
    provider_id: int
    location: int = peewee.IntegerField()

    session: MultiplayerSession = peewee.ForeignKeyField(MultiplayerSession)
    session_id: int
    receiver: World = peewee.ForeignKeyField(World)
    receiver_id: int
    time: str = peewee.DateTimeField(default=lib.datetime_now)

    class Meta:
        primary_key = peewee.CompositeKey("provider", "location")


class MultiplayerAuditEntry(BaseModel):
    session: MultiplayerSession = peewee.ForeignKeyField(MultiplayerSession, backref="audit_log")
    user: User = peewee.ForeignKeyField(User)
    message: str = peewee.TextField()
    time: str = peewee.DateTimeField(default=lib.datetime_now)

    def as_entry(self) -> AuditEntry:
        time = datetime.datetime.fromisoformat(self.time)

        return AuditEntry(
            user=self.user.name,
            message=self.message,
            time=time,
        )


class AsyncRaceTimerHolder:
    """
    Shared timer logic for the two things that can hold a race timer:
    an AsyncRaceEntry (rooms without teams) and an AsyncRaceTeam (rooms with them).

    Implementors must provide the `start_date`, `finish_date`, `paused` and `forfeit` columns,
    plus a `pauses` backref.
    """

    start_date: Any
    finish_date: Any
    paused: bool
    forfeit: bool
    submission_notes: str
    proof_url: str
    pauses: Sequence[AsyncRaceEntryPause]

    if TYPE_CHECKING:
        # Every implementor is also a BaseModel
        def save(self) -> int: ...

    @property
    def start_datetime(self) -> datetime.datetime | None:
        if self.start_date is not None:
            return datetime.datetime.fromisoformat(self.start_date)
        return None

    @start_datetime.setter
    def start_datetime(self, value: datetime.datetime | None) -> None:
        self.start_date = value

    @property
    def finish_datetime(self) -> datetime.datetime | None:
        if self.finish_date is not None:
            return datetime.datetime.fromisoformat(self.finish_date)
        return None

    @finish_datetime.setter
    def finish_datetime(self, value: datetime.datetime | None) -> None:
        self.finish_date = value

    def timer_status(self) -> async_race_room.AsyncRaceRoomUserStatus:
        """
        Calculates a AsyncRaceRoomUserStatus based on the presence of dates and flags.
        """
        if self.start_date is None:
            return async_race_room.AsyncRaceRoomUserStatus.JOINED
        elif self.forfeit:
            return async_race_room.AsyncRaceRoomUserStatus.FORFEITED
        elif self.paused:
            return async_race_room.AsyncRaceRoomUserStatus.PAUSED
        elif self.finish_date is None:
            return async_race_room.AsyncRaceRoomUserStatus.STARTED
        else:
            return async_race_room.AsyncRaceRoomUserStatus.FINISHED

    def total_pause_time(self) -> datetime.timedelta:
        return sum(
            (pause.length for pause in self.pauses if pause.length is not None),
            start=datetime.timedelta(seconds=0),
        )

    def elapsed_time(self) -> datetime.timedelta | None:
        """The final time for this run, or None if it hasn't both started and finished."""
        start = self.start_datetime
        finish = self.finish_datetime
        if start is None or finish is None:
            return None
        return finish - start - self.total_pause_time()


class AsyncRaceRoom(BaseModel):
    id: int
    name: str = peewee.CharField(max_length=MAX_SESSION_NAME_LENGTH)
    password: str | None = peewee.CharField(null=True)
    visibility: MultiplayerSessionVisibility = EnumField(
        choices=MultiplayerSessionVisibility, default=MultiplayerSessionVisibility.VISIBLE
    )
    layout_description_json: bytes = peewee.BlobField()
    game_details_json: str = peewee.CharField()
    creator: User = peewee.ForeignKeyField(User)
    creation_date: str = peewee.DateTimeField(default=lib.datetime_now)
    start_date: str = peewee.DateTimeField()
    end_date: str = peewee.DateTimeField()
    allow_pause: bool = peewee.BooleanField()
    allow_coop: bool = peewee.BooleanField(default=False)
    allow_abandon_worlds: bool = peewee.BooleanField(default=False)
    shared_team_timer: bool = peewee.BooleanField(default=True)

    entries: list[AsyncRaceEntry]
    teams: list[AsyncRaceTeam]
    audit_log: list[AsyncRaceAuditEntry]

    @property
    def layout_description(self) -> LayoutDescription:
        return LayoutDescription.from_bytes(self.layout_description_json)

    @layout_description.setter
    def layout_description(self, description: LayoutDescription) -> None:
        encoded = description.as_binary(force_spoiler=True)
        self.layout_description_json = encoded
        self.game_details_json = json.dumps(GameDetails.from_layout(description).as_json)

    def game_details(self) -> GameDetails:
        return GameDetails.from_json(json.loads(self.game_details_json))

    @property
    def world_count(self) -> int:
        return self.layout_description.world_count

    @property
    def uses_teams(self) -> bool:
        """
        Whether this room is played by teams, each in their own multiplayer session.
        """
        return async_race_room.race_uses_teams(self.world_count, self.allow_coop)

    @property
    def creation_datetime(self) -> datetime.datetime:
        return datetime.datetime.fromisoformat(self.creation_date)

    @property
    def start_datetime(self) -> datetime.datetime:
        return datetime.datetime.fromisoformat(self.start_date).replace(tzinfo=datetime.UTC)

    @start_datetime.setter
    def start_datetime(self, value: datetime.datetime | None) -> None:
        self.start_date = value

    @property
    def end_datetime(self) -> datetime.datetime:
        return datetime.datetime.fromisoformat(self.end_date).replace(tzinfo=datetime.UTC)

    @end_datetime.setter
    def end_datetime(self, value: datetime.datetime | None) -> None:
        self.end_date = value

    def get_race_status(self, now: datetime.datetime) -> AsyncRaceRoomRaceStatus:
        return AsyncRaceRoomRaceStatus.from_dates(
            self.start_datetime,
            self.end_datetime,
            now,
        )

    async def create_session_entry(self, sa: ServerApp, user: User) -> async_race_room.AsyncRaceRoomEntry:
        game_details = self.game_details()
        layout = self.layout_description

        now = lib.datetime_now()

        entry = AsyncRaceEntry.entry_for(self, user)
        own_team = entry.team if entry is not None else None

        if entry is None:
            status = async_race_room.AsyncRaceRoomUserStatus.NOT_MEMBER
        elif own_team is not None:
            status = own_team.status_for_member(entry)
        else:
            status = entry.timer_status()

        self_time = None
        if entry is not None:
            holder = entry.timer_holder()
            if holder.timer_status() == async_race_room.AsyncRaceRoomUserStatus.FINISHED:
                self_time = holder.elapsed_time()

        is_admin = bool(user == self.creator)
        own_team_id = own_team.id if own_team is not None else None
        race_status = self.get_race_status(now)
        race_is_over = race_status == async_race_room.AsyncRaceRoomRaceStatus.FINISHED
        if self.uses_teams:
            teams = [
                team.create_team_entry(
                    include_session=is_admin or team.id == own_team_id,
                    include_progress=race_is_over or team.id == own_team_id,
                )
                for team in AsyncRaceTeam.select().where(AsyncRaceTeam.room == self).order_by(AsyncRaceTeam.id)
            ]
        else:
            teams = []

        return async_race_room.AsyncRaceRoomEntry(
            id=self.id,
            name=self.name,
            visibility=self.visibility,
            creator=self.creator.name,
            creation_date=self.creation_datetime,
            start_date=self.start_datetime,
            end_date=self.end_datetime,
            race_status=race_status,
            auth_token=sa.encrypt_and_b85_dict(
                {
                    "room_id": self.id,
                    "time": now.timestamp(),
                }
            ),
            game_details=game_details,
            presets_raw=[VersionedPreset.with_preset(preset).as_bytes() for preset in layout.all_presets],
            is_admin=is_admin,
            self_status=status,
            self_time=self_time,
            allow_pause=self.allow_pause,
            world_count=layout.world_count,
            teams=teams,
            self_team_id=own_team_id,
            self_has_exported=entry.has_exported if entry is not None else False,
            self_is_captain=own_team is not None and own_team.is_captain(user),
            allow_coop=self.allow_coop,
            allow_abandon_worlds=self.allow_abandon_worlds,
            shared_team_timer=self.shared_team_timer,
        )


class AsyncRaceAuditEntry(BaseModel):
    room: AsyncRaceRoom = peewee.ForeignKeyField(AsyncRaceRoom, backref="audit_log")
    user: User = peewee.ForeignKeyField(User)
    message: str = peewee.TextField()
    time: str = peewee.DateTimeField(default=lib.datetime_now)

    def as_entry(self) -> AuditEntry:
        time = datetime.datetime.fromisoformat(self.time)

        return AuditEntry(
            user=self.user.name,
            message=self.message,
            time=time,
        )


class AsyncRaceTeam(BaseModel, AsyncRaceTimerHolder):
    """
    A group of users playing one multiworld async race together. The team holds the timer;
    its individual members only hold their join date and export state.
    """

    id: int
    room: AsyncRaceRoom = peewee.ForeignKeyField(AsyncRaceRoom, backref="teams")
    room_id: int
    name: str = peewee.CharField(max_length=MAX_SESSION_NAME_LENGTH)
    creation_date = peewee.DateTimeField(default=lib.datetime_now)
    captain: User | None = peewee.ForeignKeyField(User, null=True)
    captain_id: int | None

    start_date = peewee.DateTimeField(null=True)
    finish_date = peewee.DateTimeField(null=True)
    paused: bool = peewee.BooleanField(default=False)
    forfeit: bool = peewee.BooleanField(default=False)
    submission_notes: str = peewee.CharField(max_length=200, default="")
    proof_url: str = peewee.CharField(default="")

    members: Sequence[AsyncRaceEntry]
    pauses: Sequence[AsyncRaceEntryPause]
    sessions: Sequence[MultiplayerSession]

    @property
    def creation_datetime(self) -> datetime.datetime:
        return datetime.datetime.fromisoformat(self.creation_date)  # type: ignore[arg-type]

    @property
    def session(self) -> MultiplayerSession | None:
        """The hidden MultiplayerSession that hosts this team's multiworld."""
        for session in MultiplayerSession.select().where(MultiplayerSession.race_team == self):
            return session
        return None

    def all_members(self) -> list[AsyncRaceEntry]:
        return list(AsyncRaceEntry.select().where(AsyncRaceEntry.team == self).order_by(AsyncRaceEntry.id))

    @property
    def shared_timer(self) -> bool:
        """Whether this team runs on one shared timer, rather than accumulating its members'."""
        return self.room.shared_team_timer

    def timer_status(self) -> async_race_room.AsyncRaceRoomUserStatus:
        """
        A team on a shared timer reads its own columns. A team accumulating its members' times
        still has the captain start it and give it up, but from then on its state follows what
        the members do: it is finished once every one of them is.
        """
        if self.shared_timer:
            return AsyncRaceTimerHolder.timer_status(self)

        status = async_race_room.AsyncRaceRoomUserStatus
        if self.start_date is None:
            return status.JOINED
        if self.forfeit:
            return status.FORFEITED

        member_states = [member.timer_status() for member in self.all_members()]
        if not member_states:
            return status.STARTED
        if all(state == status.FINISHED for state in member_states):
            return status.FINISHED
        return status.STARTED

    def elapsed_time(self) -> datetime.timedelta | None:
        """
        The team's final time: the one shared timer, or the sum of every member's own time when
        the room accumulates them.
        """
        if self.shared_timer:
            return AsyncRaceTimerHolder.elapsed_time(self)

        if self.start_date is None:
            return None

        total = datetime.timedelta(seconds=0)
        for member in self.all_members():
            member_time = member.elapsed_time()
            if member_time is not None:
                total += member_time
        return total

    def status_for_member(self, entry: AsyncRaceEntry) -> async_race_room.AsyncRaceRoomUserStatus:
        """
        The status to show a given member: the team's while the timer is shared, their own once
        the race is accumulating each member's time. A forfeit is always the whole team's, so it
        covers every member no matter how the room is timed.
        """
        if self.shared_timer or self.forfeit:
            return self.timer_status()
        return entry.timer_status()

    def is_captain(self, user: User) -> bool:
        return self.captain_id == user.id

    def promote_new_captain(self) -> None:
        """Hands the captaincy to the longest-standing remaining member, if there is one."""
        members = self.all_members()
        self.captain = members[0].user if members else None
        self.save()

    def unclaimed_worlds(self) -> list[World]:
        """Worlds of this team's session that nobody has claimed yet."""
        session = self.session
        if session is None:
            return []
        return [world for world in session.get_ordered_worlds() if not list(world.associations)]

    def members_without_world(self) -> list[AsyncRaceEntry]:
        """
        Members that haven't claimed any world. With co-op a team can have more members than
        worlds, but everyone still has to be playing something.
        """
        session = self.session
        if session is None:
            return self.all_members()

        claimed_by = {
            association.user_id for world in session.get_ordered_worlds() for association in world.associations
        }
        return [member for member in self.all_members() if member.user_id not in claimed_by]

    def create_team_entry(
        self, *, include_session: bool = False, include_progress: bool = False
    ) -> async_race_room.AsyncRaceTeamEntry:
        worlds: list[async_race_room.AsyncRaceWorldEntry] = []
        session_id = None

        if include_session and (session := self.session) is not None:
            session_id = session.id
            for world in session.get_ordered_worlds():
                assert world.order is not None
                worlds.append(
                    async_race_room.AsyncRaceWorldEntry(
                        world_uuid=world.uuid,
                        order=world.order,
                        name=world.name,
                        claimed_by=[assoc.user.as_randovania_user() for assoc in world.associations],
                    )
                )

        report_time = include_progress and not self.shared_timer
        members = [
            async_race_room.AsyncRaceTeamMember(
                user=member.user.as_randovania_user(),
                status=self.status_for_member(member) if include_progress else None,
                time=member.elapsed_time() if report_time else None,
            )
            for member in self.all_members()
        ]

        captain = self.captain
        return async_race_room.AsyncRaceTeamEntry(
            id=self.id,
            name=self.name,
            status=self.timer_status() if include_progress else None,
            members=members,
            worlds=worlds,
            captain=captain.as_randovania_user() if captain is not None else None,
            session_id=session_id,
        )

    def create_admin_entry(self) -> async_race_room.AsyncRaceEntryData:
        """A team is presented to admins as a single entry, like a solo participant is."""
        members = self.all_members()
        return async_race_room.AsyncRaceEntryData(
            user=members[0].user.as_randovania_user() if members else None,
            team_id=self.id,
            team_name=self.name,
            members=[member.user.as_randovania_user() for member in members],
            join_date=self.creation_datetime,
            start_date=self.start_datetime,
            finish_date=self.finish_datetime,
            forfeit=self.forfeit,
            submission_notes=self.submission_notes,
            proof_url=self.proof_url,
            pauses=[pause.create_admin_entry() for pause in self.pauses],
        )

    def delete_with_session(self) -> None:
        """
        Deletes this team, its members' entries and the hidden session backing it.
        """
        with db.atomic():
            session = self.session
            if session is not None:
                session.delete_instance(recursive=True)
            AsyncRaceEntryPause.delete().where(AsyncRaceEntryPause.team == self).execute()
            AsyncRaceEntry.delete().where(AsyncRaceEntry.team == self).execute()
            self.delete_instance()


class AsyncRaceEntry(BaseModel, AsyncRaceTimerHolder):
    """
    One user's participation in a room. For rooms without teams this also holds the timer;
    otherwise the timer lives on the entry's team instead, since a team shares one.
    """

    id: int
    room: AsyncRaceRoom = peewee.ForeignKeyField(AsyncRaceRoom, backref="entries")
    room_id: int
    user: User = peewee.ForeignKeyField(User)
    user_id: int
    team: AsyncRaceTeam | None = peewee.ForeignKeyField(AsyncRaceTeam, null=True, backref="members")
    team_id: int | None
    join_date = peewee.DateTimeField(default=lib.datetime_now)
    start_date = peewee.DateTimeField(null=True)
    finish_date = peewee.DateTimeField(null=True)
    paused: bool = peewee.BooleanField(default=False)
    forfeit: bool = peewee.BooleanField(default=False)
    submission_notes: str = peewee.CharField(max_length=200, default="")
    proof_url: str = peewee.CharField(default="")
    has_exported: bool = peewee.BooleanField(default=False)
    pauses: Sequence[AsyncRaceEntryPause]

    class Meta:
        indexes = ((("room", "user"), True),)

    @classmethod
    def entry_for(cls, room: AsyncRaceRoom, user: User | int) -> Self | None:
        """
        Returns the entry a given user has for the given room, or None if it doesn't exist.
        """
        for entry in cls.select().where(AsyncRaceEntry.room == room, AsyncRaceEntry.user == user):
            return entry
        return None

    def timer_holder(self) -> AsyncRaceTimerHolder:
        """Whichever of this entry or its team actually owns the race timer."""
        return self.team if self.team is not None else self

    def create_admin_entry(self) -> async_race_room.AsyncRaceEntryData:
        return async_race_room.AsyncRaceEntryData(
            user=self.user.as_randovania_user(),
            team_id=None,
            team_name=None,
            members=[self.user.as_randovania_user()],
            join_date=self.join_datetime,
            start_date=self.start_datetime,
            finish_date=self.finish_datetime,
            forfeit=self.forfeit,
            submission_notes=self.submission_notes,
            proof_url=self.proof_url,
            pauses=[pause.create_admin_entry() for pause in self.pauses],
        )

    @property
    def join_datetime(self) -> datetime.datetime:
        return datetime.datetime.fromisoformat(self.join_date)  # type: ignore[arg-type]


class AsyncRaceEntryPause(BaseModel):
    """A pause of a race timer. Belongs to exactly one of an entry (solo) or a team (multiworld)."""

    entry: AsyncRaceEntry | None = peewee.ForeignKeyField(AsyncRaceEntry, null=True, backref="pauses")
    entry_id: int | None
    team: AsyncRaceTeam | None = peewee.ForeignKeyField(AsyncRaceTeam, null=True, backref="pauses")
    team_id: int | None
    start: datetime.datetime = peewee.DateTimeField(default=lib.datetime_now)
    end: datetime.datetime = peewee.DateTimeField(null=True)

    @property
    def start_datetime(self) -> datetime.datetime:
        return datetime.datetime.fromisoformat(self.start)  # type: ignore[arg-type]

    @property
    def end_datetime(self) -> datetime.datetime | None:
        if self.end is not None:
            return datetime.datetime.fromisoformat(self.end)  # type: ignore[arg-type]
        return None

    @property
    def length(self) -> datetime.timedelta | None:
        if self.end is None:
            return None
        return self.end_datetime - self.start_datetime  # type: ignore[operator]

    @classmethod
    def _owner_matches(cls, holder: AsyncRaceTimerHolder) -> Any:
        if isinstance(holder, AsyncRaceTeam):
            return cls.team == holder
        return cls.entry == holder

    @classmethod
    def create_for(cls, holder: AsyncRaceTimerHolder, start: datetime.datetime) -> Self:
        if isinstance(holder, AsyncRaceTeam):
            return cls.create(team=holder, start=start)
        return cls.create(entry=holder, start=start)

    @classmethod
    def active_pause(cls, holder: AsyncRaceTimerHolder) -> Self | None:
        for it in cls.select().where(cls._owner_matches(holder), cls.end.is_null()):  # type: ignore[attr-defined]
            return it
        return None

    def create_admin_entry(self) -> async_race_room.AsyncRacePauseEntry:
        return async_race_room.AsyncRacePauseEntry(
            start=self.start_datetime,
            end=self.end_datetime,
        )


class DiscordGuildPreferences(BaseModel):
    guild_id: int = peewee.IntegerField(primary_key=True)
    preferences_json: bytes = peewee.BlobField()

    @classmethod
    def get_with_default(cls, guild_id: int) -> DiscordGuildPreferences:
        try:
            return cls.get(guild_id)
        except cls.DoesNotExist:
            return cls.create(
                guild_id=guild_id,
                preferences_json=pydantic_util.encode_model(GuildPreferences()),
            )

    def get_preferences(self) -> GuildPreferences:
        return pydantic_util.decode_model(self.preferences_json, GuildPreferences)

    def set_preferences(self, preferences: GuildPreferences) -> None:
        self.preferences_json = pydantic_util.encode_model(preferences)


class DatabaseMigrations(enum.Enum):
    ADD_READY_TO_MEMBERSHIP = "ready_membership"
    SESSION_STATE_TO_VISIBILITY = "session_state_to_visibility"
    ADD_GAME_BEATEN = "game_beaten"
    ADD_WORLD_ABANDONED = "world_abandoned"
    ADD_ASYNC_RACE_TEAMS = "async_race_teams"
    ADD_ASYNC_RACE_SESSION_SETTINGS = "async_race_session_settings"


class PerformedDatabaseMigrations(BaseModel):
    migration = EnumField(DatabaseMigrations, unique=True)


all_classes: list[type[BaseModel]] = [
    User,
    UserAccessToken,
    MultiplayerSession,
    World,
    WorldUserAssociation,
    MultiplayerMembership,
    WorldAction,
    MultiplayerAuditEntry,
    AsyncRaceRoom,
    AsyncRaceTeam,
    AsyncRaceEntry,
    AsyncRaceEntryPause,
    AsyncRaceAuditEntry,
    # DiscordGuildPreferences,  # TODO: For later!
    PerformedDatabaseMigrations,
]


@asynccontextmanager
async def database_lifespan(_app: RdvFastAPI) -> Lifespan[MonitoredDb]:
    db_path = _app.sa.configuration["server_config"]["database_path"]
    db_existed = Path(db_path).exists()

    db.init(db_path)
    db.connect(reuse_if_open=True)

    if db_existed:
        from randovania.server import database_migration

        db.create_tables([PerformedDatabaseMigrations])
        database_migration.apply_migrations()

    db.create_tables(all_classes)

    if not db_existed:
        for entry in DatabaseMigrations:
            PerformedDatabaseMigrations.create(migration=entry)

    yield db

    db.close()
