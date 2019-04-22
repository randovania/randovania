import pytest

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder
from randovania.game_description.area_location import AreaLocation
from randovania.layout.starting_location import StartingLocationConfiguration, StartingLocation


@pytest.fixture(params=[config for config in StartingLocationConfiguration
                        if config != StartingLocationConfiguration.CUSTOM],
                name="simple_starting_location")
def _simple_starting_location(request):
    yield StartingLocation(request.param, None)


@pytest.fixture(name="custom_starting_location")
def _custom_starting_location():
    return StartingLocation(StartingLocationConfiguration.CUSTOM,
                            AreaLocation(2252328306, 3417147547))


def test_default():
    value = StartingLocation.default()

    # Assert
    assert value.configuration == StartingLocationConfiguration.SHIP


def test_round_trip_json_simple(simple_starting_location):
    # Run
    round_trip = StartingLocation.from_json(simple_starting_location.as_json)

    # Assert
    assert simple_starting_location == round_trip


def test_round_trip_json_all_custom_location(custom_starting_location):
    # Run
    round_trip = StartingLocation.from_json(custom_starting_location.as_json)

    # Assert
    assert custom_starting_location == round_trip


def test_round_trip_bitpack_simple(simple_starting_location):
    # Run
    round_trip = bitpacking.round_trip(simple_starting_location)

    # Assert
    assert simple_starting_location == round_trip


def test_round_trip_bitpack_custom_location(custom_starting_location):
    # Run
    round_trip = bitpacking.round_trip(custom_starting_location)

    # Assert
    assert custom_starting_location == round_trip


def test_invalid_constructor_missing_location():
    with pytest.raises(ValueError) as err:
        StartingLocation(StartingLocationConfiguration.CUSTOM, None)

    assert str(err.value) == "Configuration is CUSTOM, but not custom_location set"


def test_invalid_constructor_location_should_be_missing():
    with pytest.raises(ValueError) as err:
        StartingLocation(StartingLocationConfiguration.SHIP, AreaLocation(0, 0))

    assert str(err.value) == "custom_location set to world 0/area 0, " \
                             "but configuration is StartingLocationConfiguration.SHIP instead of CUSTOM"


@pytest.fixture(
    params=[
        {"encoded": b'\x00', "json": "ship"},
        {"encoded": b'@', "json": "random-save-station"},
        {"encoded": b'\x82@', "json": {"world_asset_id": 1006255871, "area_asset_id": 341957679}},
        {"encoded": b'\x92\xc0', "json": {"world_asset_id": 1039999561, "area_asset_id": 3548128276}},
    ],
    name="location_with_data")
def _location_with_data(request):
    return request.param["encoded"], StartingLocation.from_json(request.param["json"])


def test_decode(location_with_data):
    # Setup
    data, expected = location_with_data

    # Run
    decoder = BitPackDecoder(data)
    result = StartingLocation.bit_pack_unpack(decoder, {})

    # Assert
    assert result == expected


def test_encode(location_with_data):
    # Setup
    expected, value = location_with_data

    # Run
    result = bitpacking.pack_value(value)

    # Assert
    assert result == expected
