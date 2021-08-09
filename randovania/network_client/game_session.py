import dataclasses
import datetime
import json
from typing import List, Dict, Optional, Tuple

from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.binary_data import convert_to_raw_python
from randovania.games.game import RandovaniaGame
from randovania.layout.preset_migration import VersionedPreset
from randovania.network_common.binary_formats import BinaryGameSessionEntry
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
    provider: str
    provider_row: int
    receiver: str
    pickup: str
    location: PickupIndex
    time: datetime.datetime

    @classmethod
    def from_json(cls, data) -> "GameSessionAction":
        return GameSessionAction(
            provider=data["provider"],
            provider_row=data["provider_row"],
            receiver=data["receiver"],
            pickup=data["pickup"],
            location=PickupIndex(data["location"]),
            time=datetime.datetime.fromisoformat(data["time"]),
        )


@dataclasses.dataclass(frozen=True)
class GameDetails(JsonDataclass):
    seed_hash: str
    word_hash: str
    spoiler: bool
    permalink: str


@dataclasses.dataclass(frozen=True)
class GameSessionEntry:
    id: int
    name: str
    presets: List[VersionedPreset]
    players: Dict[int, PlayerSessionEntry]
    game_details: Optional[GameDetails]
    state: GameSessionState
    generation_in_progress: Optional[int]
    allowed_games: List[RandovaniaGame]

    @property
    def num_admins(self) -> int:
        return sum(1 for player in self.players.values() if player.admin)

    @property
    def num_rows(self) -> int:
        return len(self.presets)

    @classmethod
    def from_json(cls, data) -> "GameSessionEntry":
        data = convert_to_raw_python(BinaryGameSessionEntry.parse(data))

        player_entries = [
            PlayerSessionEntry.from_json(player_json)
            for player_json in data["players"]
        ]
        return GameSessionEntry(
            id=data["id"],
            name=data["name"],
            presets=[VersionedPreset(json.loads(preset_json)) for preset_json in data["presets"]],
            players={
                player_entry.id: player_entry
                for player_entry in player_entries
            },
            game_details=GameDetails.from_json(data["game_details"]) if data["game_details"] is not None else None,
            state=GameSessionState(data["state"]),
            generation_in_progress=data["generation_in_progress"],
            allowed_games=[RandovaniaGame(game) for game in data["allowed_games"]],
        )


@dataclasses.dataclass(frozen=True)
class GameSessionActions:
    actions: Tuple[GameSessionAction, ...]


@dataclasses.dataclass(frozen=True)
class GameSessionPickups:
    game: RandovaniaGame
    pickups: Tuple[Tuple[str, PickupEntry], ...]


@dataclasses.dataclass(frozen=True)
class GameSessionAuditEntry:
    user: str
    message: str
    time: datetime.datetime

    @classmethod
    def from_json(cls, data) -> "GameSessionAuditEntry":
        return GameSessionAuditEntry(
            user=data["user"],
            message=data["message"],
            time=datetime.datetime.fromisoformat(data["time"]),
        )


@dataclasses.dataclass(frozen=True)
class GameSessionAuditLog:
    entries: Tuple[GameSessionAuditEntry, ...]


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
