import dataclasses
import uuid

from frozendict import frozendict

from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.game_description.resources.item_resource_info import InventoryItem
from randovania.network_common import error
from randovania.network_common.game_connection_status import GameConnectionStatus
from randovania.network_common.multiplayer_session import MultiplayerSessionListEntry


@dataclasses.dataclass(frozen=True)
class ServerWorldSync(JsonDataclass):
    status: GameConnectionStatus
    collected_locations: tuple[int, ...]
    inventory: frozendict[str, InventoryItem] | None
    request_details: bool


@dataclasses.dataclass(frozen=True)
class ServerSyncRequest(JsonDataclass):
    worlds: frozendict[uuid.UUID, ServerWorldSync]


@dataclasses.dataclass(frozen=True)
class ServerWorldResponse(JsonDataclass):
    world_name: str
    session: MultiplayerSessionListEntry


@dataclasses.dataclass(frozen=True)
class ServerSyncResponse(JsonDataclass):
    worlds: frozendict[uuid.UUID, ServerWorldResponse]
    errors: frozendict[uuid.UUID, error.BaseNetworkError]
