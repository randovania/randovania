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
        pickup_mapping=(25, 104, 102, 50, 34, 37, 97, 16, 52, 60, 43, 40, 58, 1, 99, 74, 76, 55, 7, 8, 23, 82, 117, 88,
                        51, 61, 80, 32, 100, 101, 70, 9, 38, 71, 6, 33, 57, 66, 72, 91, 67, 56, 64, 63, 44, 3, 103, 79,
                        59, 116, 36, 0, 110, 27, 26, 106, 68, 107, 2, 31, 73, 86, 18, 89, 14, 94, 84, 30, 4, 54, 95, 19,
                        65, 12, 21, 96, 28, 105, 13, 87, 15, 115, 42, 49, 11, 112, 45, 113, 92, 10, 53, 62, 69, 24, 17,
                        77, 46, 83, 75, 108, 90, 98, 22, 29, 118, 47, 109, 39, 93, 20, 48, 81, 5, 78, 114, 85, 111, 35,
                        41),
    ),
    _create_test_layout_description(
        configuration=LayoutConfiguration(seed_number=50000,
                                          logic=LayoutLogic.NO_GLITCHES,
                                          mode=LayoutMode.STANDARD,
                                          sky_temple_keys=LayoutRandomizedFlag.RANDOMIZED,
                                          item_loss=LayoutEnabledFlag.ENABLED,
                                          elevators=LayoutRandomizedFlag.VANILLA,
                                          hundo_guaranteed=LayoutEnabledFlag.DISABLED,
                                          difficulty=LayoutDifficulty.NORMAL),
        pickup_mapping=(94, 118, 55, 80, 98, 41, 60, 107, 1, 26, 3, 92, 44, 88, 35, 32, 61, 66, 114, 73, 23, 82, 75, 46,
                        99, 10, 7, 78, 97, 37, 104, 17, 62, 28, 85, 112, 36, 72, 57, 65, 93, 115, 14, 81, 6, 13, 24, 76,
                        38, 45, 96, 74, 52, 47, 102, 16, 111, 68, 105, 84, 21, 109, 70, 49, 100, 34, 43, 51, 40, 67,
                        116, 71, 2, 83, 53, 90, 106, 91, 89, 50, 31, 30, 63, 56, 54, 103, 8, 48, 0, 5, 117, 58, 113,
                        110, 39, 69, 108, 20, 79, 4, 15, 29, 12, 33, 59, 11, 18, 95, 77, 9, 64, 101, 19, 86, 22, 27, 25,
                        42, 87),
    ),
]


@pytest.fixture(params=_test_descriptions)
def layout_description(request):
    yield request.param


def test_compare_generated_with_data(layout_description: LayoutDescription):
    debug._DEBUG_LEVEL = 0
    status_update = MagicMock()

    data = binary_data.decode_default_prime2()
    generated_description = generator.generate_list(data, layout_description.configuration, status_update=status_update)

    assert generated_description.without_solver_path == layout_description


def test_generate_twice(layout_description: LayoutDescription):
    debug._DEBUG_LEVEL = 0
    status_update = MagicMock()

    data = binary_data.decode_default_prime2()
    generated_description = generator.generate_list(data, layout_description.configuration, status_update=status_update)
    assert generated_description == generator.generate_list(data, layout_description.configuration,
                                                            status_update=status_update)
