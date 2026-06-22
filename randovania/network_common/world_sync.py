import dataclasses
import uuid

from frozendict import frozendict

from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.game_description.resources.inventory import InventoryItem
from randovania.network_common import error
from randovania.network_common.game_connection_status import GameConnectionStatus
from randovania.network_common.signals.common import TypedBytes


@dataclasses.dataclass(frozen=True)
class ServerWorldSync:
    status: GameConnectionStatus
    collected_locations: tuple[int, ...]
    inventory: TypedBytes[frozendict[str, InventoryItem]] | None
    request_details: bool
    has_been_beaten: bool


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
