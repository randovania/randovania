import datetime
import functools
import json
from typing import Iterator, List, Optional, Callable, Any

import peewee

from randovania.game_description import default_database
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.game import RandovaniaGame
from randovania.layout.layout_description import LayoutDescription
from randovania.layout.preset import Preset
from randovania.layout.preset_migration import VersionedPreset
from randovania.network_common.binary_formats import BinaryGameSessionEntry, BinaryGameSessionActions
from randovania.network_common.session_state import GameSessionState

db = peewee.SqliteDatabase(None, pragmas={'foreign_keys': 1})


class BaseModel(peewee.Model):
    class Meta:
        database = db
        legacy_table_names = False


class EnumField(peewee.CharField):
    """
    This class enable an Enum like field for Peewee
    """

    def __init__(self, choices: Callable, *args: Any, **kwargs: Any) -> None:
        super(peewee.CharField, self).__init__(*args, **kwargs)
        self.choices = choices
        self.max_length = 255

    def db_value(self, value: Any) -> Any:
        return value.value

    def python_value(self, value: Any) -> Any:
        return self.choices(type(list(self.choices)[0].value)(value))


class User(BaseModel):
    discord_id = peewee.IntegerField(index=True, null=True)
    name = peewee.CharField()
    admin = peewee.BooleanField(default=False)

    @classmethod
    def get_by_id(cls, pk) -> "User":
        return cls.get(cls._meta.primary_key == pk)

    @property
    def as_json(self):
        return {
            "id": self.id,
            "name": self.name,
        }


@functools.lru_cache()
def _decode_layout_description(s):
    return LayoutDescription.from_json_dict(json.loads(s))


def _datetime_now():
    return datetime.datetime.now(datetime.timezone.utc)


class GameSession(BaseModel):
    name = peewee.CharField()
    password = peewee.CharField(null=True)
    state = EnumField(choices=GameSessionState, default=GameSessionState.SETUP)
    layout_description_json = peewee.TextField(null=True)
    seed_hash = peewee.CharField(null=True)
    creator = peewee.ForeignKeyField(User)
    creation_date = peewee.DateTimeField(default=_datetime_now)
    generation_in_progress = peewee.ForeignKeyField(User, null=True)
    dev_features = peewee.CharField(null=True)

    @property
    def all_presets(self) -> List[Preset]:
        return [
            VersionedPreset(json.loads(preset.preset)).get_preset()
            for preset in sorted(self.presets, key=lambda it: it.row)
        ]

    @property
    def num_rows(self) -> int:
        return len(self.presets)

    @property
    def layout_description(self) -> Optional[LayoutDescription]:
        # FIXME: a server can have an invalid layout description. Likely from an old version!
        return _decode_layout_description(self.layout_description_json) if self.layout_description_json else None

    @layout_description.setter
    def layout_description(self, description: Optional[LayoutDescription]):
        self.layout_description_json = json.dumps(description.as_json) if description is not None else None

    @property
    def creation_datetime(self) -> datetime.datetime:
        return datetime.datetime.fromisoformat(self.creation_date)

    def create_list_entry(self):
        return {
            "id": self.id,
            "name": self.name,
            "has_password": self.password is not None,
            "state": self.state.value,
            "num_players": len(self.players),
            "creator": self.creator.name,
            "creation_date": self.creation_datetime.astimezone(datetime.timezone.utc).isoformat(),
        }

    @property
    def allowed_games(self) -> List[RandovaniaGame]:
        games = [RandovaniaGame.METROID_PRIME, RandovaniaGame.METROID_PRIME_ECHOES]

        if "prime3" in (self.dev_features or ""):
            games.append(RandovaniaGame.METROID_PRIME_CORRUPTION)

        return games

    def describe_actions(self):
        description = self.layout_description
        location_to_name = {
            row: f"Player {row + 1}" for row in range(self.num_rows)
        }
        for membership in self.players:
            if not membership.is_observer:
                location_to_name[membership.row] = membership.effective_name

        def _describe_action(action: GameSessionTeamAction) -> dict:
            provider: int = action.provider_row
            receiver: int = action.receiver_row
            provider_location_index = PickupIndex(action.provider_location_index)
            time = datetime.datetime.fromisoformat(action.time)
            target = description.all_patches[provider].pickup_assignment[provider_location_index]

            return {
                "provider": location_to_name[provider],
                "provider_row": provider,
                "receiver": location_to_name[receiver],
                "pickup": target.pickup.name,
                "location": provider_location_index.index,
                "time": time.astimezone(datetime.timezone.utc).isoformat(),
            }

        return BinaryGameSessionActions.build([
            _describe_action(action)
            for action in GameSessionTeamAction.select().where(GameSessionTeamAction.session == self
                                                               ).order_by(GameSessionTeamAction.time.asc())
        ])

    def create_session_entry(self):
        description = self.layout_description

        game_details = None
        if description is not None:
            game_details = {
                "spoiler": description.permalink.spoiler,
                "word_hash": description.shareable_word_hash,
                "seed_hash": description.shareable_hash,
                "permalink": description.permalink.as_base64_str,
            }

        return BinaryGameSessionEntry.build({
            "id": self.id,
            "name": self.name,
            "state": self.state.value,
            "players": [
                membership.as_json
                for membership in self.players
            ],
            "presets": [
                preset.preset
                for preset in sorted(self.presets, key=lambda it: it.row)
            ],
            "game_details": game_details,
            "generation_in_progress": (self.generation_in_progress.id
                                       if self.generation_in_progress is not None else None),
            "allowed_games": [game.value for game in self.allowed_games],
        })

    def reset_layout_description(self):
        self.layout_description_json = None
        self.save()


class GameSessionPreset(BaseModel):
    session = peewee.ForeignKeyField(GameSession, backref="presets")
    row = peewee.IntegerField()
    preset = peewee.TextField()

    class Meta:
        primary_key = peewee.CompositeKey('session', 'row')


class GameSessionMembership(BaseModel):
    user = peewee.ForeignKeyField(User, backref="games")
    session = peewee.ForeignKeyField(GameSession, backref="players")
    row = peewee.IntegerField(null=True)
    admin = peewee.BooleanField()
    join_date = peewee.DateTimeField(default=_datetime_now)
    connection_state = peewee.TextField(null=True)
    inventory = peewee.BlobField(null=True)

    @property
    def as_json(self):
        return {
            "id": self.user.id,
            "name": self.user.name,
            "row": self.row,
            "admin": self.admin,
            # "inventory": self.inventory,
            "connection_state": self.connection_state,
        }

    @property
    def effective_name(self) -> str:
        return self.user.name

    @property
    def is_observer(self) -> bool:
        return self.row is None

    @classmethod
    def get_by_ids(cls, user_id: int, session_id: int) -> "GameSessionMembership":
        return GameSessionMembership.get(
            GameSessionMembership.session == session_id,
            GameSessionMembership.user == user_id,
        )

    @classmethod
    def get_by_session_position(cls, session: GameSession, row: int) -> "GameSessionMembership":
        return GameSessionMembership.get(
            GameSessionMembership.session == session,
            GameSessionMembership.row == row,
        )

    @classmethod
    def non_observer_members(cls, session: GameSession) -> Iterator["GameSessionMembership"]:
        yield from GameSessionMembership.select().where(GameSessionMembership.session == session,
                                                        GameSessionMembership.row != None,
                                                        )

    class Meta:
        primary_key = peewee.CompositeKey('user', 'session')
        constraints = [peewee.SQL('UNIQUE(session_id, row)')]


class GameSessionTeamAction(BaseModel):
    session = peewee.ForeignKeyField(GameSession)
    provider_row = peewee.IntegerField()
    provider_location_index = peewee.IntegerField()
    receiver_row = peewee.IntegerField()

    time = peewee.DateTimeField(default=_datetime_now)

    class Meta:
        primary_key = peewee.CompositeKey('session', 'provider_row', 'provider_location_index')


all_classes = [User, GameSession, GameSessionPreset, GameSessionMembership, GameSessionTeamAction]
