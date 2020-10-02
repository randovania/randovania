import datetime
import functools
import json
from typing import Iterator, List, Optional, Callable, Any

import peewee

from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.layout.layout_description import LayoutDescription
from randovania.layout.preset import Preset
from randovania.network_common.session_state import GameSessionState

db = peewee.SqliteDatabase(None, pragmas={'foreign_keys': 1})


class BaseModel(peewee.Model):
    class Meta:
        database = db


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

    @property
    def all_presets(self) -> List[Preset]:
        return [
            Preset.from_json_dict(json.loads(preset.preset))
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

    def create_list_entry(self):
        return {
            "id": self.id,
            "name": self.name,
            "has_password": self.password is not None,
            "state": self.state.value,
            "num_players": len(self.players),
            "creator": self.creator.name,
        }

    def create_session_entry(self):
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
            time = datetime.datetime.fromisoformat(action.time)
            target = description.all_patches[provider].pickup_assignment[PickupIndex(action.provider_location_index)]

            message = (f"{location_to_name[provider]} found {target.pickup.name} "
                       f"for {location_to_name[receiver]}.")
            return {
                "message": message,
                "time": time.astimezone(datetime.timezone.utc).isoformat(),
            }

        return {
            "id": self.id,
            "name": self.name,
            "state": self.state.value,
            "players": [
                {
                    "id": membership.user.id,
                    "name": membership.user.name,
                    "row": membership.row,
                    "is_observer": membership.is_observer,
                    "admin": membership.admin,
                }
                for membership in self.players
            ],
            "presets": [
                json.loads(preset.preset)
                for preset in sorted(self.presets, key=lambda it: it.row)
            ],
            "actions": [
                _describe_action(action)
                for action in GameSessionTeamAction.select().where(GameSessionTeamAction.session == self
                                                                   ).order_by(GameSessionTeamAction.time.asc())
            ],
            "spoiler": description.permalink.spoiler if description is not None else None,
            "word_hash": description.shareable_word_hash if description is not None else None,
            "seed_hash": description.shareable_hash if description is not None else None,
            "generation_in_progress": (self.generation_in_progress.id
                                       if self.generation_in_progress is not None else None),
        }

    def reset_layout_description(self):
        self.layout_description_json = None
        self.save()


class GameSessionPreset(BaseModel):
    session = peewee.ForeignKeyField(GameSession, backref="presets")
    row = peewee.IntegerField()
    preset = peewee.TextField()


class GameSessionMembership(BaseModel):
    user = peewee.ForeignKeyField(User, backref="games")
    session = peewee.ForeignKeyField(GameSession, backref="players")
    row = peewee.IntegerField()
    is_observer = peewee.BooleanField()
    admin = peewee.BooleanField()
    join_date = peewee.DateTimeField(default=_datetime_now)
    inventory = peewee.TextField(null=True)

    @property
    def effective_name(self) -> str:
        return self.user.name

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
            GameSessionMembership.is_observer == False,
        )

    @classmethod
    def non_observer_members(cls, session: GameSession) -> Iterator["GameSessionMembership"]:
        yield from GameSessionMembership.select().where(GameSessionMembership.session == session,
                                                        GameSessionMembership.is_observer == False,
                                                        )

    class Meta:
        primary_key = peewee.CompositeKey('user', 'session')


class GameSessionTeamAction(BaseModel):
    session = peewee.ForeignKeyField(GameSession)
    provider_row = peewee.IntegerField()
    provider_location_index = peewee.IntegerField()
    receiver_row = peewee.IntegerField()

    time = peewee.DateTimeField(default=_datetime_now)

    class Meta:
        primary_key = peewee.CompositeKey('session', 'provider_row', 'provider_location_index')


all_classes = [User, GameSession, GameSessionPreset, GameSessionMembership, GameSessionTeamAction]
