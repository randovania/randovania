from __future__ import annotations

import collections
import datetime
import enum
import json
import uuid
import zlib
from typing import TYPE_CHECKING, Any, Self

import cachetools
import peewee
from sentry_sdk.tracing_utils import record_sql_queries

from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.game import RandovaniaGame
from randovania.layout.layout_description import LayoutDescription
from randovania.layout.versioned_preset import VersionedPreset
from randovania.network_common import error, multiplayer_session
from randovania.network_common.game_connection_status import GameConnectionStatus
from randovania.network_common.multiplayer_session import (
    MAX_SESSION_NAME_LENGTH,
    MAX_WORLD_NAME_LENGTH,
    GameDetails,
    MultiplayerSessionAuditEntry,
    MultiplayerSessionAuditLog,
    MultiplayerUser,
    MultiplayerWorld,
    UserWorldDetail,
)
from randovania.network_common.session_visibility import MultiplayerSessionVisibility

if TYPE_CHECKING:
    from collections.abc import Iterable


class MonitoredDb(peewee.SqliteDatabase):
    def execute_sql(self, sql, params=None, commit=peewee.SENTINEL):
        with record_sql_queries(self.cursor, sql, params, paramstyle="format", executemany=False):
            return super().execute_sql(sql, params, commit)


db = MonitoredDb(None, pragmas={"foreign_keys": 1})


def is_boolean(field, value: bool):
    return field == value


class BaseModel(peewee.Model):
    class Meta:
        database = db
        legacy_table_names = False

    @classmethod
    def create(cls, **query) -> Self:
        return super().create(**query)

    @classmethod
    def get(cls, *query, **filters) -> Self:
        return super().get(*query, **filters)

    @classmethod
    def get_by_id(cls, pk) -> Self:
        return super().get_by_id(pk)

    @classmethod
    def get_or_create(cls, **kwargs) -> tuple[Self, bool]:
        return super().get_or_create(**kwargs)


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

    @property
    def as_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "discord_id": self.discord_id,
        }


def _datetime_now():
    return datetime.datetime.now(datetime.UTC)


class UserAccessToken(BaseModel):
    user = peewee.ForeignKeyField(User, backref="access_tokens")
    name = peewee.CharField()
    creation_date = peewee.DateTimeField(default=_datetime_now)
    last_used = peewee.DateTimeField(default=_datetime_now)

    class Meta:
        primary_key = peewee.CompositeKey("user", "name")


@cachetools.cached(cache=cachetools.TTLCache(maxsize=64, ttl=600))
def _decode_layout_description(layout: bytes, presets: tuple[str, ...]) -> LayoutDescription:
    preset_list = [VersionedPreset.from_str(preset) for preset in presets]
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
    creation_date = peewee.DateTimeField(default=_datetime_now)
    generation_in_progress: User | None = peewee.ForeignKeyField(User, null=True)
    dev_features: str | None = peewee.CharField(null=True)

    allow_coop: bool = peewee.BooleanField(default=False)
    allow_everyone_claim_world: bool = peewee.BooleanField(default=False)

    members: list[MultiplayerMembership]
    worlds: list[World]
    audit_log: list[MultiplayerAuditEntry]

    def has_layout_description(self) -> bool:
        return self.layout_description_json is not None

    def _get_layout_description(self, ordered_worlds: list[World]) -> LayoutDescription:
        return _decode_layout_description(self.layout_description_json, tuple(world.preset for world in ordered_worlds))

    @property
    def layout_description(self) -> LayoutDescription | None:
        if self.layout_description_json is not None:
            return self._get_layout_description(self.get_ordered_worlds())
        else:
            return None

    @layout_description.setter
    def layout_description(self, description: LayoutDescription | None):
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
        if self.layout_description_json is not None:
            # TODO: just return layout_description_json directly!
            return self.layout_description.as_binary(include_presets=False, force_spoiler=True)
        else:
            return None

    def game_details(self) -> GameDetails | None:
        if self.game_details_json is not None:
            return GameDetails.from_json(json.loads(self.game_details_json))
        return None

    @property
    def creation_datetime(self) -> datetime.datetime:
        return datetime.datetime.fromisoformat(self.creation_date)

    def is_user_in_session(self, user: User):
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
        return list(World.select().where(World.session == self).order_by(World.order.asc()))

    def describe_actions(self):
        if not self.has_layout_description():
            return multiplayer_session.MultiplayerSessionActions(self.id, [])

        worlds = self.get_ordered_worlds()
        description: LayoutDescription = self._get_layout_description(worlds)
        world_by_id = {world.get_id(): world for world in worlds}

        def _describe_action(action: WorldAction) -> multiplayer_session.MultiplayerSessionAction:
            provider = world_by_id[action.provider_id]
            receiver = world_by_id[action.receiver_id]

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
                preset_raw=world.preset,
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
    uuid: uuid.UUID = peewee.UUIDField(default=uuid.uuid4, unique=True)

    name: str = peewee.CharField(max_length=MAX_WORLD_NAME_LENGTH)
    preset: str = peewee.TextField()
    order: int | None = peewee.IntegerField(null=True, default=None)

    associations: list[WorldUserAssociation]

    @classmethod
    def get_by_uuid(cls, uid) -> World:
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
        uid: uuid.UUID | None = None,
        order: int | None = None,
    ) -> Self:
        if uid is None:
            uid = uuid.uuid4()
        return cls().create(
            session=session,
            uuid=uid,
            name=name,
            preset=json.dumps(preset.as_json, separators=(",", ":")),
            order=order,
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
    last_activity: datetime.datetime = peewee.DateTimeField(default=_datetime_now)
    inventory = peewee.BlobField(null=True)

    @classmethod
    def get_by_instances(cls, *, world: World | int, user: User | int) -> Self:
        return cls.get(
            WorldUserAssociation.world == world,
            WorldUserAssociation.user == user,
        )

    @classmethod
    def get_by_ids(cls, world_uid: uuid.UUID, user_id: int) -> Self:
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
    join_date = peewee.DateTimeField(default=_datetime_now)

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
    time: str = peewee.DateTimeField(default=_datetime_now)

    class Meta:
        primary_key = peewee.CompositeKey("provider", "location")


class MultiplayerAuditEntry(BaseModel):
    session: MultiplayerSession = peewee.ForeignKeyField(MultiplayerSession, backref="audit_log")
    user: User = peewee.ForeignKeyField(User)
    message: str = peewee.TextField()
    time: str = peewee.DateTimeField(default=_datetime_now)

    def as_entry(self) -> MultiplayerSessionAuditEntry:
        time = datetime.datetime.fromisoformat(self.time)

        return MultiplayerSessionAuditEntry(
            user=self.user.name,
            message=self.message,
            time=time,
        )


class DatabaseMigrations(enum.Enum):
    ADD_READY_TO_MEMBERSHIP = "ready_membership"
    SESSION_STATE_TO_VISIBILITY = "session_state_to_visibility"


class PerformedDatabaseMigrations(BaseModel):
    migration = EnumField(DatabaseMigrations, unique=True)


all_classes = [
    User,
    UserAccessToken,
    MultiplayerSession,
    World,
    WorldUserAssociation,
    MultiplayerMembership,
    WorldAction,
    MultiplayerAuditEntry,
    PerformedDatabaseMigrations,
]
