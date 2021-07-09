import itertools

import pytest

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder
from randovania.game_description.world.area_location import AreaLocation
from randovania.games.game import RandovaniaGame
from randovania.layout.lib.location_list import LocationList


@pytest.fixture(
    params=[
        {"encoded": b'\x00', "json": []},
        {"encoded": b'\x0c\x00', "json": [{"world_asset_id": 1006255871, "area_asset_id": 1655756413}]},
        {"encoded": b'\x14\x84', "json": [
            {"world_asset_id": 1006255871, "area_asset_id": 3098756660},
            {"world_asset_id": 1006255871, "area_asset_id": 3997643454}
        ]},
    ],
    name="location_with_data")
def _location_with_data(request, mocker, echoes_game_description):
    world_list = echoes_game_description.world_list
    areas = list(itertools.islice(
        (AreaLocation(world.world_asset_id, area.area_asset_id)
         for world in world_list.worlds
         for area in world.areas
         if area.valid_starting_location), 15))

    mocker.patch("randovania.layout.lib.location_list.LocationList.areas_list",
                 return_value=list(sorted(areas)))
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
