import itertools

import pytest

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder
from randovania.game_description.area_location import AreaLocation
from randovania.games.game import RandovaniaGame
from randovania.layout.starting_location import StartingLocation


@pytest.fixture(
    params=[
        {"encoded": b'\x00', "json": []},
        {"encoded": b'\x0c\x00', "json": ["Temple Grounds/Landing Site"]},
        {"encoded": b'\x14\x84', "json": ["Temple Grounds/Hall of Honored Dead", "Temple Grounds/Path of Eyes"]},
    ],
    name="location_with_data")
def _location_with_data(request, mocker, echoes_game_description):
    world_list = echoes_game_description.world_list
    areas = list(itertools.islice(
        (AreaLocation(world.world_asset_id, area.area_asset_id)
         for world in world_list.worlds
         for area in world.areas
         if area.valid_starting_location), 15))

    mocker.patch("randovania.layout.starting_location._areas_list",
                 return_value=list(sorted(areas)))
    return request.param["encoded"], StartingLocation.from_json(request.param["json"], RandovaniaGame.PRIME2)


def test_decode(location_with_data):
    # Setup
    data, expected = location_with_data

    # Run
    decoder = BitPackDecoder(data)
    result = StartingLocation.bit_pack_unpack(
        decoder, {"reference": StartingLocation.with_elements([], RandovaniaGame.PRIME2)})

    # Assert
    assert result == expected


def test_encode(location_with_data):
    # Setup
    expected, value = location_with_data

    # Run
    result = bitpacking.pack_value(value)

    # Assert
    assert result == expected
