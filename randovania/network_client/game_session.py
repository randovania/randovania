import dataclasses
import datetime
from typing import List, Dict, Optional

from randovania.layout.preset_migration import VersionedPreset
from randovania.network_common.session_state import GameSessionState


@dataclasses.dataclass(frozen=True)
class GameSessionListEntry:
    id: int
    name: str
    has_password: bool
    state: GameSessionState
    num_players: int
    creator: str
    creation_date: datetime.datetime

    def __post_init__(self):
        tzinfo = self.creation_date.tzinfo
        assert tzinfo is not None and tzinfo.utcoffset(self.creation_date) is not None

    @classmethod
    def from_json(cls, data: dict) -> "GameSessionListEntry":
        data["state"] = GameSessionState(data["state"])
        data["creation_date"] = datetime.datetime.fromisoformat(data["creation_date"])
        return GameSessionListEntry(**data)


@dataclasses.dataclass(frozen=True)
class PlayerSessionEntry:
    id: int
    name: str
    row: Optional[int]
    admin: bool
    connection_state: str

    @classmethod
    def from_json(cls, data) -> "PlayerSessionEntry":
        return PlayerSessionEntry(
            id=data["id"],
            name=data["name"],
            row=data["row"],
            admin=data["admin"],
            connection_state=data["connection_state"],
        )

    @property
    def is_observer(self):
        return self.row is None


@dataclasses.dataclass(frozen=True)
class GameSessionAction:
    message: str
    time: datetime.datetime

    @classmethod
    def from_json(cls, data) -> "GameSessionAction":
        return GameSessionAction(
            message=data["message"],
            time=datetime.datetime.fromisoformat(data["time"]),
        )


@dataclasses.dataclass(frozen=True)
class GameSessionEntry:
    id: int
    name: str
    presets: List[VersionedPreset]
    players: Dict[int, PlayerSessionEntry]
    actions: List[GameSessionAction]
    seed_hash: Optional[str]
    word_hash: Optional[str]
    spoiler: Optional[bool]
    permalink: Optional[str]
    state: GameSessionState
    generation_in_progress: Optional[int]

    @property
    def num_admins(self) -> int:
        return sum(1 for player in self.players.values() if player.admin)

    @property
    def num_rows(self) -> int:
        return len(self.presets)

    @classmethod
    def from_json(cls, data) -> "GameSessionEntry":
        player_entries = [
            PlayerSessionEntry.from_json(player_json)
            for player_json in data["players"]
        ]
        return GameSessionEntry(
            id=data["id"],
            name=data["name"],
            presets=[VersionedPreset(preset_json) for preset_json in data["presets"]],
            players={
                player_entry.id: player_entry
                for player_entry in player_entries
            },
            actions=[GameSessionAction.from_json(item) for item in data["actions"]],
            seed_hash=data["seed_hash"],
            word_hash=data["word_hash"],
            spoiler=data["spoiler"],
            permalink=data["permalink"],
            state=GameSessionState(data["state"]),
            generation_in_progress=data["generation_in_progress"],
        )


@dataclasses.dataclass(frozen=True)
class User:
    id: int
    name: str

    @classmethod
    def from_json(cls, data) -> "User":
        return cls(
            id=data["id"],
            name=data["name"],
        )

    @property
    def as_json(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
        }
