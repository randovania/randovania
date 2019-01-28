import pytest

from randovania.bitpacking import bitpacking
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

    assert str(err.value) == "custom_location set to AreaLocation(world_asset_id=0, area_asset_id=0), " \
                             "but configuration is ship instead of CUSTOM"
