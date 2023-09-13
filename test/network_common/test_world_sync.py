from __future__ import annotations

import uuid

from frozendict import frozendict

from randovania.bitpacking import construct_pack
from randovania.network_common import error, world_sync
from randovania.network_common.game_connection_status import GameConnectionStatus
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
        worlds=frozendict(
            {
                uuid.UUID("2fb143a7-f48b-41d0-915a-0276a021f558"): world_sync.ServerWorldSync(
                    status=GameConnectionStatus.Disconnected,
                    collected_locations=(1, 2, 5),
                    inventory=None,
                    request_details=True,
                ),
            }
        )
    )

    encoded = construct_pack.encode(request)

    assert encoded == b"\x01/\xb1C\xa7\xf4\x8bA\xd0\x91Z\x02v\xa0!\xf5X\x00\x03\x02\x04\n\x00\x01"


def test_encode_sync_response():
    response = world_sync.ServerSyncResponse(
        worlds=frozendict(
            {
                uuid.UUID("268e8d33-38cc-4a9b-b73f-419fada748b7"): ServerWorldResponse(
                    world_name="World",
                    session_id=5,
                    session_name="Our Session",
                ),
            }
        ),
        errors=frozendict(
            {
                uuid.UUID("9755efc7-77e4-4711-8f03-ba71c366ef81"): error.ServerError(),
            }
        ),
    )

    encoded = construct_pack.encode(response)

    assert encoded == (
        b"\x01&\x8e\x8d38\xccJ\x9b\xb7?A\x9f\xad\xa7H\xb7\x05World\n\x01\x0bOur Sessio"
        b'n\x01\x97U\xef\xc7w\xe4G\x11\x8f\x03\xbaq\xc3f\xef\x81"{"error":{"code"'
        b':6,"detail":null}}'
    )
