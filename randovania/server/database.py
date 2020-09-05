import datetime
import functools
import json
from typing import Iterator, List, Optional

import peewee

from randovania.layout.layout_description import LayoutDescription
from randovania.layout.preset import Preset

db = peewee.SqliteDatabase('test.db', pragmas={'foreign_keys': 1})


class BaseModel(peewee.Model):
    class Meta:
        database = db


class User(BaseModel):
    discord_id = peewee.IntegerField(index=True, null=True)
    name = peewee.CharField()

    @property
    def as_json(self):
        return {
            "id": self.id,
            "name": self.name,
        }


@functools.lru_cache()
def _decode_layout_description(s):
    return LayoutDescription.from_json_dict(json.loads(s))


class GameSession(BaseModel):
    name = peewee.CharField()
    password = peewee.CharField(null=True)
    num_teams = peewee.IntegerField()
    in_game = peewee.BooleanField(default=False)
    layout_description_json = peewee.TextField(null=True)
    seed_hash = peewee.CharField(null=True)
    creation_date = peewee.DateTimeField(default=datetime.datetime.now)

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
            "in_game": self.in_game,
            "num_players": len(self.players)
        }

    def create_session_entry(self):
        description = self.layout_description
        return {
            "id": self.id,
            "name": self.name,
            "num_teams": self.num_teams,
            "in_game": self.in_game,
            "players": [
                {
                    "id": membership.user.id,
                    "name": membership.user.name,
                    "row": membership.row,
                    "team": membership.team,
                    "admin": membership.admin,
                }
                for membership in self.players
            ],
            "presets": [
                json.loads(preset.preset)
                for preset in sorted(self.presets, key=lambda it: it.row)
            ],
            "spoiler": description.permalink.spoiler if description is not None else None,
            "word_hash": description.shareable_word_hash if description is not None else None,
            "seed_hash": description.shareable_hash if description is not None else None,
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
    team = peewee.IntegerField(null=True)
    admin = peewee.BooleanField()
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
    def get_by_session_position(cls, session: GameSession, row: int, team: int) -> "GameSessionMembership":
        return GameSessionMembership.get(
            GameSessionMembership.session == session,
            GameSessionMembership.row == row,
            GameSessionMembership.team == team,
        )

    @classmethod
    def members_for_team(cls, session: GameSession, team: int) -> Iterator["GameSessionMembership"]:
        yield from GameSessionMembership.select().where(GameSessionMembership.session == session,
                                                        GameSessionMembership.team == team
                                                        )

    class Meta:
        primary_key = peewee.CompositeKey('user', 'session')


class GameSessionTeamAction(BaseModel):
    session = peewee.ForeignKeyField(GameSession)
    team = peewee.IntegerField()
    provider_row = peewee.IntegerField()
    provider_location_index = peewee.IntegerField()
    receiver_row = peewee.IntegerField()

    time = peewee.DateTimeField(default=datetime.datetime.now)

    class Meta:
        primary_key = peewee.CompositeKey('session', 'team', 'provider_row', 'provider_location_index')


db.connect(reuse_if_open=True)
db.create_tables([User, GameSession, GameSessionPreset, GameSessionMembership, GameSessionTeamAction])

# user = db.User.create(name="Zero", discord_id=0)
# session = db.GameSession.create(name="Race", password=None, num_teams=1)
# db.GameSessionMembership.create(user=user, session=session, row=0, team=0)
