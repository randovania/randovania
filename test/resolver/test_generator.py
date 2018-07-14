from unittest.mock import MagicMock

import pytest

from randovania.games.prime import binary_data
from randovania.resolver import generator, debug
from randovania.resolver.layout_configuration import LayoutConfiguration, LayoutLogic, LayoutMode, LayoutRandomizedFlag, \
    LayoutEnabledFlag, LayoutDifficulty
from randovania.resolver.layout_description import LayoutDescription


def _create_test_layout_description(
        configuration: LayoutConfiguration,
        pickup_mapping):
    return LayoutDescription(
        configuration=configuration,
        version='0.9.2',
        pickup_mapping=pickup_mapping,
        solver_path=())


def _remove_solver_path(description: LayoutDescription):
    return LayoutDescription(
        configuration=description.configuration,
        version=description.version,
        pickup_mapping=description.pickup_mapping,
        solver_path=())


_test_descriptions = [
    _create_test_layout_description(
        configuration=LayoutConfiguration(seed_number=1027649936,
                                          logic=LayoutLogic.NO_GLITCHES,
                                          mode=LayoutMode.STANDARD,
                                          sky_temple_keys=LayoutRandomizedFlag.RANDOMIZED,
                                          item_loss=LayoutEnabledFlag.ENABLED,
                                          elevators=LayoutRandomizedFlag.VANILLA,
                                          hundo_guaranteed=LayoutEnabledFlag.DISABLED,
                                          difficulty=LayoutDifficulty.NORMAL),
        pickup_mapping=(81, 14, 74, 29, 75, 102, 88, 106, 38, 118, 31, 82, 48, 113, 7, 67, 101, 15, 99, 117, 36, 23, 57,
                        89, 10, 66, 107, 45, 25, 49, 111, 93, 53, 35, 28, 51, 37, 73, 54, 97, 22, 77, 44, 80, 5, 104,
                        112, 33, 46, 100, 83, 76, 52, 62, 103, 17, 40, 58, 70, 4, 116, 98, 63, 32, 110, 71, 50, 69, 90,
                        91, 68, 19, 16, 11, 27, 6, 95, 56, 18, 79, 26, 12, 94, 84, 41, 96, 8, 2, 105, 114, 13, 65, 1,
                        87, 30, 109, 21, 64, 3, 34, 39, 92, 72, 55, 43, 59, 0, 24, 115, 108, 78, 86, 60, 42, 9, 20, 47,
                        85, 61),
    )
]


@pytest.fixture(params=_test_descriptions)
def layout_description(request):
    yield request.param


def test_compare_generated_with_data(layout_description: LayoutDescription):
    debug._DEBUG_LEVEL = 0
    status_update = MagicMock()

    data = binary_data.decode_default_prime2()
    generated_description = generator.generate_list(data, layout_description.configuration, status_update=status_update)

    assert _remove_solver_path(generated_description) == layout_description


def test_generate_twice(layout_description: LayoutDescription):
    debug._DEBUG_LEVEL = 0
    status_update = MagicMock()

    data = binary_data.decode_default_prime2()
    generated_description = generator.generate_list(data, layout_description.configuration, status_update=status_update)
    assert generated_description == generator.generate_list(data, layout_description.configuration, status_update=status_update)
