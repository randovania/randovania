import itertools

import pytest

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder
from randovania.game_description.world.area_identifier import AreaIdentifier
from randovania.game_description.world.node_identifier import NodeIdentifier
from randovania.games.game import RandovaniaGame
from randovania.layout.lib.location_list import LocationList


@pytest.fixture(
    params=[
        {"encoded": b'\x00', "json": []},
        {"encoded": b'\x0cP', "json": [{"world_name": "Temple Grounds", "area_name": "Landing Site", "node_name": "Save Station"}]},
        {"encoded": b'\x12\x8a', "json": [
            {"world_name": "Temple Grounds", "area_name": "Hall of Honored Dead", "node_name": "Door to Path of Honor"},
            {"world_name": "Temple Grounds", "area_name": "Path of Eyes", "node_name": "Portal from Abandoned Base"}
        ]},
    ],
    name="location_with_data")
def _location_with_data(request, mocker, echoes_game_description):
    world_list = echoes_game_description.world_list
    nodes = list(itertools.islice(
        (NodeIdentifier.create(world.name, area.name, node.name)
         for world in world_list.worlds
         for area in world.areas
         for node in area.actual_nodes
         if area.has_start_node() and node.valid_starting_location), 15))

    mocker.patch("randovania.layout.lib.location_list.LocationList.nodes_list",
                 return_value=list(sorted(nodes)))
    return request.param["encoded"], LocationList.from_json(request.param["json"], RandovaniaGame.METROID_PRIME_ECHOES)


def test_decode(location_with_data):
    # Setup
    data, expected = location_with_data

    # Run
    decoder = BitPackDecoder(data)
    result = LocationList.bit_pack_unpack(
        decoder, {"reference": LocationList.with_elements([], RandovaniaGame.METROID_PRIME_ECHOES)})

    # Assert
    assert result == expected


def test_encode(location_with_data):
    # Setup
    expected, value = location_with_data

    # Run
    result = bitpacking.pack_value(value)

    # Assert
    assert result == expected
