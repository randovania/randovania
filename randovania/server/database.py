from __future__ import annotations

import datetime
import enum
import json
import uuid
import zlib
from typing import Any, Self, Iterable

import cachetools
import peewee
import sentry_sdk
from sentry_sdk.tracing_utils import record_sql_queries

from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.game import RandovaniaGame
from randovania.layout.layout_description import LayoutDescription
from randovania.layout.versioned_preset import VersionedPreset
from randovania.network_common import multiplayer_session, error
from randovania.network_common.game_connection_status import GameConnectionStatus
from randovania.network_common.multiplayer_session import MultiplayerUser, GameDetails, \
    MultiplayerWorld, MultiplayerSessionListEntry, MultiplayerSessionAuditLog, \
    MultiplayerSessionAuditEntry, UserWorldDetail, MAX_SESSION_NAME_LENGTH, MAX_WORLD_NAME_LENGTH
from randovania.network_common.session_state import MultiplayerSessionState


class MonitoredDb(peewee.SqliteDatabase):
    def execute_sql(self, sql, params=None, commit=peewee.SENTINEL):
        with record_sql_queries(
                sentry_sdk.Hub.current, self.cursor, sql, params, paramstyle="format", executemany=False
        ):
            return super().execute_sql(sql, params, commit)


db = MonitoredDb(None, pragmas={'foreign_keys': 1})


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
    return datetime.datetime.now(datetime.timezone.utc)


class UserAccessToken(BaseModel):
    user = peewee.ForeignKeyField(User, backref="access_tokens")
    name = peewee.CharField()
    creation_date = peewee.DateTimeField(default=_datetime_now)
    last_used = peewee.DateTimeField(default=_datetime_now)

    class Meta:
        primary_key = peewee.CompositeKey('user', 'name')


@cachetools.cached(cache=cachetools.TTLCache(maxsize=64, ttl=600))
def _decode_layout_description(layout: bytes, presets: tuple[str, ...]) -> LayoutDescription:
    decoded = json.loads(zlib.decompress(layout).decode("utf-8"))
    decoded["info"]["presets"] = [
        VersionedPreset.from_str(preset).as_json
        for preset in presets
    ]
    return LayoutDescription.from_json_dict(decoded)


class MultiplayerSession(BaseModel):
    id: int
    name: str = peewee.CharField(max_length=MAX_SESSION_NAME_LENGTH)
    password: str | None = peewee.CharField(null=True)
    state: MultiplayerSessionState = EnumField(choices=MultiplayerSessionState,
                                               default=MultiplayerSessionState.SETUP)
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

    @property
    def layout_description(self) -> LayoutDescription | None:
        if self.layout_description_json is not None:
            return _decode_layout_description(
                self.layout_description_json,
                tuple(world.preset for world in self.get_ordered_worlds())
            )
        else:
            return None

    @layout_description.setter
    def layout_description(self, description: LayoutDescription | None):
        if description is not None:
            encoded = description.as_json(force_spoiler=True)
            encoded["info"].pop("presets")
            self.layout_description_json = zlib.compress(
                json.dumps(encoded, separators=(',', ':')).encode("utf-8")
            )
            self.game_details_json = json.dumps(GameDetails(
                spoiler=description.has_spoiler,
                word_hash=description.shareable_word_hash,
                seed_hash=description.shareable_hash,
            ).as_json)
        else:
            self.layout_description_json = None
            self.game_details_json = None

    @property
    def creation_datetime(self) -> datetime.datetime:
        return datetime.datetime.fromisoformat(self.creation_date)

    def is_user_in_session(self, user: User):
        try:
            MultiplayerMembership.get_by_ids(user, self.id)
        except peewee.DoesNotExist:
            return False
        return True

    def create_list_entry(self, user: User):
        return MultiplayerSessionListEntry(
            id=self.id,
            name=self.name,
            has_password=self.password is not None,
            state=self.state,
            num_players=len(self.members),
            creator=self.creator.name,
            creation_date=self.creation_datetime,
            is_user_in_session=self.is_user_in_session(user),
        )

    @property
    def allowed_games(self) -> list[RandovaniaGame]:
        dev_features = self.dev_features or ""
        return [
            game for game in RandovaniaGame.sorted_all_games()
            if game.data.defaults_available_in_game_sessions or game.value in dev_features
        ]

    def get_ordered_worlds(self) -> list[World]:
        return list(World.select().where(World.session == self
                                         ).order_by(World.order.asc()))

    def describe_actions(self):
        if not self.has_layout_description():
            return multiplayer_session.MultiplayerSessionActions(self.id, [])

        description: LayoutDescription = self.layout_description

        worlds = self.get_ordered_worlds()
        world_by_id = {
            world.id: world
            for world in worlds
        }

        def _describe_action(action: WorldAction) -> multiplayer_session.MultiplayerSessionAction:
            provider = world_by_id[action.provider.id]
            receiver = world_by_id[action.receiver.id]

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
                for action in WorldAction.select().where(WorldAction.session == self
                                                         ).order_by(WorldAction.time.asc())
            ],
        )

    def create_session_entry(self) -> multiplayer_session.MultiplayerSessionEntry:
        game_details = None
        if self.game_details_json is not None:
            game_details = GameDetails.from_json(json.loads(self.game_details_json))

        return multiplayer_session.MultiplayerSessionEntry(
            id=self.id,
            name=self.name,
            state=self.state,
            users_list=[
                MultiplayerUser(
                    id=member.user.id,
                    name=member.user.name,
                    admin=member.admin,
                    worlds={
                        association.world.uuid: UserWorldDetail(
                            connection_state=association.connection_state,
                            last_activity=association.last_activity,
                        )
                        for association in WorldUserAssociation.find_all_for_user_in_session(
                            member.user.id, self.id,
                        )
                    },
                )
                for member in self.members
            ],
            worlds=[
                MultiplayerWorld(
                    id=world.uuid,
                    name=world.name,
                    preset_raw=world.preset,
                )
                for world in self.worlds
            ],
            game_details=game_details,
            generation_in_progress=(self.generation_in_progress.id
                                    if self.generation_in_progress is not None else None),
            allowed_games=self.allowed_games,
        )

    def get_audit_log(self) -> MultiplayerSessionAuditLog:
        return MultiplayerSessionAuditLog(
            session_id=self.id,
            entries=[
                entry.as_entry()
                for entry in self.audit_log
            ]
        )


class World(BaseModel):
    id: int
    session: MultiplayerSession = peewee.ForeignKeyField(MultiplayerSession, backref="worlds")
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
            raise error.WorldDoesNotExistError()

    @classmethod
    def get_by_order(cls, session_id: int, order: int) -> World:
        return cls.get(
            World.session == session_id,
            World.order == order,
        )

    @classmethod
    def create_for(cls, session: MultiplayerSession, name: str, preset: VersionedPreset, *,
                   uid: "uuid.UUID | None" = None, order: int | None = None) -> Self:
        if uid is None:
            uid = uuid.uuid4()
        return cls().create(
            session=session,
            uuid=uid,
            name=name,
            preset=json.dumps(preset.as_json, separators=(',', ':')),
            order=order,
        )


class WorldUserAssociation(BaseModel):
    """A given user's association to one given row."""
    world: World = peewee.ForeignKeyField(World, backref="associations")
    user: User = peewee.ForeignKeyField(User)

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
        return cls.select().join(World).where(
            World.uuid == world_uid,
            WorldUserAssociation.user == user_id,
        ).get()

    @classmethod
    def find_all_for_user_in_session(cls, user_id: int, session_id: int) -> Iterable[Self]:
        yield from cls.select().join(World).where(
            World.session == session_id,
            WorldUserAssociation.user == user_id,
        )

    class Meta:
        primary_key = peewee.CompositeKey('world', 'user')


class MultiplayerMembership(BaseModel):
    user: User = peewee.ForeignKeyField(User, backref="sessions")
    session: MultiplayerSession = peewee.ForeignKeyField(MultiplayerSession, backref="members")
    admin: bool = peewee.BooleanField(default=False)
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
        primary_key = peewee.CompositeKey('user', 'session')


class WorldAction(BaseModel):
    provider: World = peewee.ForeignKeyField(World, backref="actions")
    location: int = peewee.IntegerField()

    session: MultiplayerSession = peewee.ForeignKeyField(MultiplayerSession)
    receiver: World = peewee.ForeignKeyField(World)
    time: str = peewee.DateTimeField(default=_datetime_now)

    class Meta:
        primary_key = peewee.CompositeKey('provider', 'location')


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


all_classes = [
    User, UserAccessToken, MultiplayerSession, World,
    WorldUserAssociation, MultiplayerMembership,
    WorldAction, MultiplayerAuditEntry,
]
