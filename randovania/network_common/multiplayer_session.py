from __future__ import annotations

import dataclasses
import datetime
import re
import uuid

from randovania.bitpacking import construct_pack
from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.game_description.resources.item_resource_info import InventoryItem
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.game import RandovaniaGame
from randovania.network_common.game_connection_status import GameConnectionStatus
from randovania.network_common.session_state import MultiplayerSessionState


MAX_SESSION_NAME_LENGTH = 50
MAX_WORLD_NAME_LENGTH = 30

WORLD_NAME_RE = re.compile(
    r"^[a-zA-Z0-9 _\-!?]{1," + str(MAX_WORLD_NAME_LENGTH) + "}$"
)


@dataclasses.dataclass(frozen=True)
class MultiplayerSessionListEntry(JsonDataclass):
    id: int
    name: str
    has_password: bool
    state: MultiplayerSessionState
    num_players: int
    creator: str
    creation_date: datetime.datetime
    is_user_in_session: bool

    def __post_init__(self):
        tzinfo = self.creation_date.tzinfo
        assert tzinfo is not None and tzinfo.utcoffset(self.creation_date) is not None


@dataclasses.dataclass(frozen=True)
class UserWorldDetail(JsonDataclass):
    connection_state: GameConnectionStatus
    last_activity: datetime.datetime


@dataclasses.dataclass(frozen=True)
class MultiplayerUser(JsonDataclass):
    id: int
    name: str
    admin: bool
    worlds: dict[uuid.UUID, UserWorldDetail]


@dataclasses.dataclass()
class MultiplayerWorld(JsonDataclass):
    id: uuid.UUID
    name: str
    preset_raw: str


@dataclasses.dataclass(frozen=True)
class MultiplayerWorldPickups:
    world_id: uuid.UUID
    game: RandovaniaGame
    pickups: tuple[tuple[str, PickupEntry], ...]


@dataclasses.dataclass(frozen=True)
class MultiplayerSessionAction(JsonDataclass):
    provider: uuid.UUID
    receiver: uuid.UUID
    pickup: str
    location: int
    time: datetime.datetime

    @property
    def location_index(self):
        return PickupIndex(self.location)


@dataclasses.dataclass(frozen=True)
class MultiplayerSessionActions(JsonDataclass):
    session_id: int
    actions: list[MultiplayerSessionAction]  # TODO: use tuple


@dataclasses.dataclass(frozen=True)
class GameDetails(JsonDataclass):
    seed_hash: str
    word_hash: str
    spoiler: bool


@dataclasses.dataclass(frozen=True)
class MultiplayerSessionEntry(JsonDataclass):
    id: int
    name: str
    worlds: list[MultiplayerWorld]
    users_list: list[MultiplayerUser]
    game_details: GameDetails | None
    state: MultiplayerSessionState
    generation_in_progress: int | None
    allowed_games: list[RandovaniaGame]

    @property
    def users(self) -> dict[int, MultiplayerUser]:
        return {
            user.id: user
            for user in self.users_list
        }

    @property
    def num_admins(self) -> int:
        return sum(1 for player in self.users.values() if player.admin)

    def get_world(self, world_id: uuid.UUID) -> MultiplayerWorld:
        for world in self.worlds:
            if world.id == world_id:
                return world
        raise KeyError(f"No world with id {world_id}")


@dataclasses.dataclass(frozen=True)
class MultiplayerSessionAuditEntry(JsonDataclass):
    user: str
    message: str
    time: datetime.datetime


@dataclasses.dataclass(frozen=True)
class MultiplayerSessionAuditLog(JsonDataclass):
    session_id: int
    entries: list[MultiplayerSessionAuditEntry]  # TODO: restore tuple


RemoteInventory = dict[str, InventoryItem]


@dataclasses.dataclass(frozen=True)
class WorldUserInventory:
    world_id: uuid.UUID
    user_id: int
    inventory: RemoteInventory


@dataclasses.dataclass(frozen=True)
class User:
    id: int
    name: str
    discord_id: int | None = None

    @classmethod
    def from_json(cls, data) -> "User":
        return cls(
            id=data["id"],
            name=data["name"],
            discord_id=data.get("discord_id"),
        )

    @property
    def as_json(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "discord_id": self.discord_id,
        }


BinaryInventory = construct_pack.construct_for_type(WorldUserInventory)
