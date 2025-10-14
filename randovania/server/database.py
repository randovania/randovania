# mypy: disable-error-code="assignment"

from __future__ import annotations

import collections
import datetime
import enum
import hashlib
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
from randovania.layout.base.base_configuration import BaseConfiguration
from randovania.layout.layout_description import LayoutDescription
from randovania.layout.versioned_preset import VersionedPreset
from randovania.network_common import async_race_room, error, multiplayer_session
from randovania.network_common.async_race_room import AsyncRaceRoomRaceStatus
from randovania.network_common.audit import AuditEntry
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

        def order_by(self, *values: Any) -> Self: ...

        def join(self, dest: Any, join_type: Any = None, on: Any = None) -> Any: ...

        def count(self, clear_limit: bool = False) -> int: ...

        def __iter__(self) -> Iterator[T]: ...

        def paginate(self, page_number: int, items_per_page: int) -> Self: ...


class MonitoredDb(peewee.SqliteDatabase):
    def execute_sql(self, sql, params=None, commit=peewee.SENTINEL):  # type: ignore[no-untyped-def]
        with record_sql_queries(self.cursor, sql, params, paramstyle="format", executemany=False):
            return super().execute_sql(sql, params, commit)


db = MonitoredDb(None, pragmas={"foreign_keys": 1})


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
        return self.choices(type(list(self.choices)[0].value)(value))


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


class PresetData(BaseModel):
    sha256: bytes = peewee.BlobField(primary_key=True)
    content: bytes = peewee.BlobField()
    schema_version: int = peewee.IntegerField()
    game: str = peewee.CharField()

    def get_preset(self) -> VersionedPreset[BaseConfiguration]:
        return VersionedPreset[BaseConfiguration].from_bytes(self.content)

    @classmethod
    def create_for_preset(cls, preset: VersionedPreset[BaseConfiguration], preset_bytes: bytes | None = None) -> Self:
        """
        Creates a PresetData from the given preset.

        :param preset: The preset to use.
        :param preset_bytes: The preset's as_bytes, if you already have it.
        :return: Reuses any existing instance with the same hash.
        """
        if preset_bytes is None:
            preset_bytes = preset.as_bytes()
        preset_hash = hashlib.sha256(preset_bytes).digest()

        try:
            game_str = preset.game.value
        except ValueError:
            # Unknown game
            game_str = preset.data["game"]

        return cls.get_or_create(
            sha256=preset_hash,
            content=preset_bytes,
            schema_version=preset.schema_version,
            game=game_str,
        )[0]

    @classmethod
    def create_for_bytes(cls, preset_bytes: bytes) -> Self:
        """
        Creates a PresetData from a preset decoded from the given bytes.
        Reuses any existing instance with the same hash.
        """
        preset = VersionedPreset[BaseConfiguration].from_bytes(preset_bytes)
        return cls.create_for_preset(preset, preset_bytes)

    @classmethod
    def create_for_json(cls, preset_json: JsonObject) -> Self:
        """
        Creates a PresetData from a preset json object.
        Reuses any existing instance with the same hash.
        """
        preset = VersionedPreset[BaseConfiguration](preset_json)
        return cls.create_for_preset(preset)


@cachetools.cached(cache=cachetools.TTLCache(maxsize=64, ttl=600))
def _decode_layout_description(layout: bytes, presets: tuple[bytes, ...]) -> LayoutDescription:
    preset_list: list[VersionedPreset] = [VersionedPreset.from_bytes(preset) for preset in presets]
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

    members: list[MultiplayerMembership]
    worlds: list[World]
    audit_log: list[MultiplayerAuditEntry]

    def has_layout_description(self) -> bool:
        return self.layout_description_json is not None

    def set_layout_description(self, description: LayoutDescription | None) -> None:
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

    def get_layout_description(self, ordered_worlds: list[World] | None = None) -> LayoutDescription | None:
        if self.layout_description_json is not None:
            if ordered_worlds is None:
                ordered_worlds = self.get_ordered_worlds()

            return _decode_layout_description(
                self.layout_description_json, tuple(world.preset_data.content for world in ordered_worlds)
            )
        else:
            return None

    def get_layout_description_as_json(self) -> dict | None:
        """Get the stored LayoutDescription as a JSON object"""
        if self.layout_description_json is not None:
            return LayoutDescription.bytes_to_dict(
                self.layout_description_json,
                presets=[VersionedPreset.from_str(world.preset) for world in self.get_ordered_worlds()],
            )
        return None

    def get_layout_description_as_binary(self) -> bytes | None:
        # Technically it should be the following. But trusting the db is correct is a lot faster!
        # self.get_layout_description().as_binary(include_presets=False, force_spoiler=True)
        return self.layout_description_json

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
        return list(
            World.select(
                World.id,
                World.order,
                World.uuid,
                World.name,
                World.beaten,
                World.preset_data,
                PresetData.content,
            )
            .join(PresetData, on=World.preset_data)
            .where(World.session == self)
            .order_by(World.order.asc())  # type: ignore[union-attr]
        )

    def describe_actions(self) -> multiplayer_session.MultiplayerSessionActions:
        if not self.has_layout_description():
            return multiplayer_session.MultiplayerSessionActions(self.id, [])

        worlds = self.get_ordered_worlds()
        description: LayoutDescription = self.get_layout_description(worlds)
        world_by_id = {world.get_id(): world for world in worlds}

        def _describe_action(action: WorldAction) -> multiplayer_session.MultiplayerSessionAction:
            provider = world_by_id[action.provider_id]
            receiver = world_by_id[action.receiver_id]

            assert provider.order is not None

            location_index = PickupIndex(action.location)
            target = description.all_patches[provider.order].pickup_assignment[location_index]

            return multiplayer_session.MultiplayerSessionAction(
                provider=provider.uuid,
                receiver=receiver.uuid,
                pickup=target.pickup.name,
                location=action.location,
                time=datetime.datetime.fromisoformat(action.time),
            )

        return multiplayer_session.MultiplayerSessionActions(
            self.id,
            [
                _describe_action(action)
                for action in WorldAction.select().where(WorldAction.session == self).order_by(WorldAction.time.asc())
                # type: ignore[attr-defined]
            ],
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
                preset_raw=world.preset_data.content,
                has_been_beaten=world.beaten,
            )
            for world in self.get_ordered_worlds()
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
    preset_data: PresetData | None = peewee.ForeignKeyField(PresetData, null=True)

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
        preset_bytes: bytes,
        *,
        uid: UUID | None = None,
        order: int | None = None,
        beaten: bool = False,
    ) -> Self:
        if uid is None:
            uid = uuid.uuid4()

        return cls().create(
            session=session,
            uuid=uid,
            name=name,
            preset="",
            preset_data=PresetData.create_for_bytes(preset_bytes),
            order=order,
            beaten=beaten,
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

    entries: list[AsyncRaceEntry]
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
    def creation_datetime(self) -> datetime.datetime:
        return datetime.datetime.fromisoformat(self.creation_date)

    @property
    def start_datetime(self) -> datetime.datetime:
        return datetime.datetime.fromisoformat(self.start_date)

    @start_datetime.setter
    def start_datetime(self, value: datetime.datetime | None) -> None:
        self.start_date = value

    @property
    def end_datetime(self) -> datetime.datetime:
        return datetime.datetime.fromisoformat(self.end_date)

    @end_datetime.setter
    def end_datetime(self, value: datetime.datetime | None) -> None:
        self.end_date = value

    def get_race_status(self, now: datetime.datetime) -> AsyncRaceRoomRaceStatus:
        return AsyncRaceRoomRaceStatus.from_dates(
            self.start_datetime,
            self.end_datetime,
            now,
        )

    async def create_session_entry(self, sa: ServerApp, sid: str) -> async_race_room.AsyncRaceRoomEntry:
        game_details = self.game_details()

        now = lib.datetime_now()
        for_user = await sa.get_current_user(sid)

        if (entry := AsyncRaceEntry.entry_for(self, for_user)) is not None:
            status = entry.user_status()
        else:
            status = async_race_room.AsyncRaceRoomUserStatus.NOT_MEMBER

        return async_race_room.AsyncRaceRoomEntry(
            id=self.id,
            name=self.name,
            visibility=self.visibility,
            creator=self.creator.name,
            creation_date=self.creation_datetime,
            start_date=self.start_datetime,
            end_date=self.end_datetime,
            race_status=self.get_race_status(now),
            auth_token=sa.encrypt_dict(
                {
                    "room_id": self.id,
                    "time": now.timestamp(),
                }
            ),
            game_details=game_details,
            presets_raw=[
                VersionedPreset.with_preset(preset).as_bytes() for preset in self.layout_description.all_presets
            ],
            is_admin=for_user == self.creator,  # type: ignore[arg-type]
            self_status=status,
            allow_pause=self.allow_pause,
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


class AsyncRaceEntry(BaseModel):
    room: AsyncRaceRoom = peewee.ForeignKeyField(AsyncRaceRoom, backref="entries")
    user: User = peewee.ForeignKeyField(User)
    user_id: int
    join_date = peewee.DateTimeField(default=lib.datetime_now)
    start_date = peewee.DateTimeField(null=True)
    finish_date = peewee.DateTimeField(null=True)
    paused: bool = peewee.BooleanField(default=False)
    forfeit: bool = peewee.BooleanField(default=False)
    submission_notes: str = peewee.CharField(max_length=200, default="")
    proof_url: str = peewee.CharField(default="")
    pauses: Sequence[AsyncRaceEntryPause]

    @classmethod
    def entry_for(cls, room: AsyncRaceRoom, user: User | int) -> Self | None:
        """
        Returns the entry a given user has for the given room, or None if it doesn't exist.
        """
        for entry in cls.select().where(AsyncRaceEntry.room == room, AsyncRaceEntry.user == user):
            return entry
        return None

    def user_status(self) -> async_race_room.AsyncRaceRoomUserStatus:
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

    def create_admin_entry(self) -> async_race_room.AsyncRaceEntryData:
        return async_race_room.AsyncRaceEntryData(
            user=self.user.as_randovania_user(),
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

    @property
    def start_datetime(self) -> datetime.datetime | None:
        if self.start_date is not None:
            return datetime.datetime.fromisoformat(self.start_date)  # type: ignore[arg-type]
        return None

    @start_datetime.setter
    def start_datetime(self, value: datetime.datetime | None) -> None:
        self.start_date = value

    @property
    def finish_datetime(self) -> datetime.datetime | None:
        if self.finish_date is not None:
            return datetime.datetime.fromisoformat(self.finish_date)  # type: ignore[arg-type]
        return None

    @finish_datetime.setter
    def finish_datetime(self, value: datetime.datetime | None) -> None:
        self.finish_date = value


class AsyncRaceEntryPause(BaseModel):
    entry: AsyncRaceEntry = peewee.ForeignKeyField(AsyncRaceEntry, backref="pauses")
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
    def active_pause(cls, entry: AsyncRaceEntry) -> Self | None:
        for it in cls.select().where(cls.entry == entry, cls.end.is_null()):  # type: ignore[attr-defined]
            return it
        return None

    def create_admin_entry(self) -> async_race_room.AsyncRacePauseEntry:
        return async_race_room.AsyncRacePauseEntry(
            start=self.start_datetime,
            end=self.end_datetime,
        )


class DatabaseMigrations(enum.Enum):
    ADD_READY_TO_MEMBERSHIP = "ready_membership"
    SESSION_STATE_TO_VISIBILITY = "session_state_to_visibility"
    ADD_GAME_BEATEN = "game_beaten"
    ADD_WORLD_PRESET_SHA256 = "add_world_preset_sha256"
    MIGRATE_WORLD_PRESET = "migrate_world_preset"


class PerformedDatabaseMigrations(BaseModel):
    migration = EnumField(DatabaseMigrations, unique=True)


all_classes: list[type[BaseModel]] = [
    User,
    UserAccessToken,
    MultiplayerSession,
    PresetData,
    World,
    WorldUserAssociation,
    MultiplayerMembership,
    WorldAction,
    MultiplayerAuditEntry,
    AsyncRaceRoom,
    AsyncRaceEntry,
    AsyncRaceEntryPause,
    AsyncRaceAuditEntry,
    PerformedDatabaseMigrations,
]


@asynccontextmanager
async def database_lifespan(_app: RdvFastAPI) -> Lifespan[MonitoredDb]:
    db_path = _app.sa.configuration["server_config"]["database_path"]
    db_existed = Path(db_path).exists()

    db.init(db_path)
    db.connect(reuse_if_open=True)
    db.create_tables(all_classes)

    if not db_existed:
        for entry in DatabaseMigrations:
            PerformedDatabaseMigrations.create(migration=entry)

    from randovania.server import database_migration

    database_migration.apply_migrations()

    yield db

    db.close()
