from __future__ import annotations

import uuid

from randovania.interface_common.world_database import CURRENT_VERSION, WorldData, WorldDatabase
from randovania.lib import json_lib


async def test_load_existing_data(tmp_path):
    uid1 = "00000000-0000-0000-2222-000000000000"
    uid2 = "00000000-0000-0000-3333-000000000000"

    persist = tmp_path.joinpath("persist")
    persist.mkdir()

    json_lib.write_path(persist.joinpath(f"{uid1}.json"), {"schema_version": 1, "data": {}})
    json_lib.write_path(persist.joinpath(f"{uid2}.json"), {"schema_version": 1, "data": {}})
    json_lib.write_path(persist.joinpath(f"2/{uid2}.json"), {"schema_version": 2, "data": {"was_game_beaten": True}})
    json_lib.write_path(
        persist.joinpath(f"{CURRENT_VERSION + 1}/{uid1}.json"), {"schema_version": 2, "data": {"bad_data": True}}
    )

    # Run
    client = WorldDatabase(persist)
    await client.load_existing_data()

    # Assert
    assert client._all_data == {uuid.UUID(uid1): WorldData(), uuid.UUID(uid2): WorldData(was_game_beaten=True)}
    assert list(client.all_known_data()) == [
        uuid.UUID(uid2),
        uuid.UUID(uid1),
    ]


async def test_set_data_for(tmp_path):
    uid = uuid.UUID("00000000-0000-0000-2222-000000000000")

    persist = tmp_path.joinpath("persist")
    data = WorldData()

    # Run
    client = WorldDatabase(persist)
    await client.set_data_for(uid, data)

    # Assert
    assert json_lib.read_path(persist.joinpath(str(CURRENT_VERSION), f"{uid}.json")) == {
        "schema_version": CURRENT_VERSION,
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
