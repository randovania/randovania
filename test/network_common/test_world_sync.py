import datetime
import uuid

from frozendict import frozendict

from randovania.bitpacking import construct_pack
from randovania.network_common import world_sync, error
from randovania.network_common.game_connection_status import GameConnectionStatus
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

    encoded = construct_pack.encode(request)

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

    encoded = construct_pack.encode(request)

    assert encoded == b'\x01/\xb1C\xa7\xf4\x8bA\xd0\x91Z\x02v\xa0!\xf5X\x00\x03\x02\x04\n\x00\x01'


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
                    is_user_in_session=True,
                ),
            ),
        }),
        errors=frozendict({
            uuid.UUID('9755efc7-77e4-4711-8f03-ba71c366ef81'): error.ServerError(),
        }),
    )

    encoded = construct_pack.encode(response)

    assert encoded == (
        b'\x01&\x8e\x8d38\xccJ\x9b\xb7?A\x9f\xad\xa7H\xb7\x05World\n\x0bOur Session'
        b'\x01\x01\x04\x07Not You\x80\xa0\xcc\xf1\x8c\xa3\xb78\x01\x01\x97U\xef\xc7'
        b'w\xe4G\x11\x8f\x03\xbaq\xc3f\xef\x81"{"error":{"code":6,"detail":null}}'
    )
