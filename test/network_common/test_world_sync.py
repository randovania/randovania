import datetime
import uuid

from frozendict import frozendict

from randovania.bitpacking import construct_dataclass
from randovania.game_connection.connector_builder_choice import ConnectorBuilderChoice
from randovania.network_common.game_connection_status import GameConnectionStatus
from randovania.network_common import world_sync, error
from randovania.network_common.multiplayer_session import MultiplayerSessionListEntry
from randovania.network_common.session_state import MultiplayerSessionState
from randovania.network_common.world_sync import ServerWorldResponse


def test_encode_world_sync():
    request = world_sync.ServerWorldSync(
        status=GameConnectionStatus.Disconnected,
        collected_locations=(),
        inventory=None,
        request_details=True,
    )

    encoded = construct_dataclass.encode_json_dataclass(request)

    assert encoded == b"\x00\x00\x00\x01"


def test_encode_sync_request():
    request = world_sync.ServerSyncRequest(
        worlds=frozendict({
            uuid.UUID("2fb143a7-f48b-41d0-915a-0276a021f558"): world_sync.ServerWorldSync(
                status=GameConnectionStatus.Disconnected,
                collected_locations=(1, 2, 5),
                inventory=None,
                request_details=True,
            ),
        })
    )

    encoded = construct_dataclass.encode_json_dataclass(request)

    assert encoded == b"\x012fb143a7-f48b-41d0-915a-0276a021f558\x00\x03\x02\x04\n\x00\x01"


def test_encode_sync_response():
    response = world_sync.ServerSyncResponse(
        worlds=frozendict({
            uuid.UUID('268e8d33-38cc-4a9b-b73f-419fada748b7'): ServerWorldResponse(
                world_name="World",
                session=MultiplayerSessionListEntry(
                    id=5,
                    name="Our Session",
                    has_password=True,
                    state=MultiplayerSessionState.IN_PROGRESS,
                    num_players=2,
                    creator="Not You",
                    creation_date=datetime.datetime(2020, 5, 2, 10, 20, tzinfo=datetime.timezone.utc),
                ),
            ),
        }),
        errors=frozendict({
            uuid.UUID('9755efc7-77e4-4711-8f03-ba71c366ef81'): error.ServerError(),
        }),
    )

    encoded = construct_dataclass.encode_json_dataclass(response)

    assert encoded == (
        b'\x01268e8d33-38cc-4a9b-b73f-419fada748b7\x05World\n\x0bOur Session'
        b'\x01\x01\x04\x07Not You\x192020-05-02T10:20:00+00:00\x019755efc7-77e4-4711'
        b'-8f03-ba71c366ef81&{"error": {"code": 6, "detail": null}}'
    )
