from __future__ import annotations

import uuid

from randovania.interface_common.world_database import WorldData, WorldDatabase
from randovania.lib import json_lib


async def test_load_existing_data(tmp_path):
    uid = "00000000-0000-0000-2222-000000000000"

    persist = tmp_path.joinpath("persist")
    persist.mkdir()

    json_lib.write_path(persist.joinpath(f"{uid}.json"), {"schema_version": 1, "data": {}})

    # Run
    client = WorldDatabase(persist)
    await client.load_existing_data()

    # Assert
    assert client._all_data == {uuid.UUID(uid): WorldData()}
    assert list(client.all_known_data()) == [uuid.UUID(uid)]


async def test_set_data_for(tmp_path):
    uid = uuid.UUID("00000000-0000-0000-2222-000000000000")

    persist = tmp_path.joinpath("persist")
    data = WorldData()

    # Run
    client = WorldDatabase(persist)
    await client.set_data_for(uid, data)

    # Assert
    assert json_lib.read_path(persist.joinpath(f"{uid}.json")) == {
        "schema_version": 1,
        "data": data.as_json,
    }
    assert client.get_data_for(uid) == data


async def test_get_locations_to_upload(tmp_path):
    uid = uuid.UUID("00000000-0000-0000-2222-000000000000")

    persist = tmp_path.joinpath("persist")
    data = WorldData(collected_locations=(10, 50), uploaded_locations=(50,))
    client = WorldDatabase(persist)
    client._all_data[uid] = data

    # Run
    result = client.get_locations_to_upload(uid)

    # Assert
    assert result == (10,)
