import dataclasses
from typing import List, Dict, Optional

from randovania.layout.preset import Preset


@dataclasses.dataclass(frozen=True)
class GameSessionListEntry:
    id: int
    name: str
    has_password: bool
    in_game: bool
    num_players: int


@dataclasses.dataclass(frozen=True)
class PlayerSessionEntry:
    id: int
    name: str
    row: int
    team: Optional[int]
    admin: bool

    @classmethod
    def from_json(cls, data) -> "PlayerSessionEntry":
        return PlayerSessionEntry(
            id=data["id"],
            name=data["name"],
            row=data["row"],
            team=data["team"],
            admin=data["admin"],
        )


@dataclasses.dataclass(frozen=True)
class GameSessionEntry:
    id: int
    name: str
    num_teams: int
    presets: List[Preset]
    players: Dict[int, PlayerSessionEntry]
    seed_hash: Optional[str]
    word_hash: Optional[str]
    spoiler: Optional[bool]

    @property
    def num_admins(self) -> int:
        return sum(1 for player in self.players.values() if player.admin)

    @classmethod
    def from_json(cls, data) -> "GameSessionEntry":
        return GameSessionEntry(
            id=data["id"],
            name=data["name"],
            num_teams=data["num_teams"],
            presets=[Preset.from_json_dict(preset_json) for preset_json in data["presets"]],
            players={
                player_json["id"]: PlayerSessionEntry.from_json(player_json)
                for player_json in data["players"]
            },
            seed_hash=data["seed_hash"],
            word_hash=data["word_hash"],
            spoiler=data["spoiler"],
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
