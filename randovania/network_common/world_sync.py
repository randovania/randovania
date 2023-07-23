import dataclasses
import uuid

from frozendict import frozendict

from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.network_common import error
from randovania.network_common.game_connection_status import GameConnectionStatus


@dataclasses.dataclass(frozen=True)
class ServerWorldSync:
    status: GameConnectionStatus
    collected_locations: tuple[int, ...]
    inventory: bytes | None  # frozendict[str, InventoryItem], but pre-encoded
    request_details: bool


@dataclasses.dataclass(frozen=True)
class ServerSyncRequest:
    worlds: frozendict[uuid.UUID, ServerWorldSync]


@dataclasses.dataclass(frozen=True)
class ServerWorldResponse(JsonDataclass):
    world_name: str
    session_id: int
    session_name: str | None


@dataclasses.dataclass(frozen=True)
class ServerSyncResponse(JsonDataclass):
    worlds: frozendict[uuid.UUID, ServerWorldResponse]
    errors: frozendict[uuid.UUID, error.BaseNetworkError]
