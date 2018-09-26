from unittest.mock import MagicMock

import pytest

from randovania.games.prime import binary_data
from randovania.resolver import generator, debug
from randovania.resolver.layout_configuration import LayoutConfiguration, LayoutLogic, LayoutMode, LayoutRandomizedFlag, \
    LayoutEnabledFlag, LayoutDifficulty
from randovania.resolver.layout_description import LayoutDescription


def _create_test_layout_description(
        seed_number: int,
        configuration: LayoutConfiguration,
        pickup_mapping):
    return LayoutDescription(
        seed_number=seed_number,
        configuration=configuration,
        version='0.12.1',
        pickup_mapping=pickup_mapping,
        solver_path=())


_test_descriptions = [
    _create_test_layout_description(
        seed_number=1027649936,
        configuration=LayoutConfiguration(logic=LayoutLogic.NO_GLITCHES,
                                          mode=LayoutMode.STANDARD,
                                          sky_temple_keys=LayoutRandomizedFlag.RANDOMIZED,
                                          item_loss=LayoutEnabledFlag.ENABLED,
                                          elevators=LayoutRandomizedFlag.VANILLA,
                                          hundo_guaranteed=LayoutEnabledFlag.DISABLED,
                                          difficulty=LayoutDifficulty.NORMAL),
        pickup_mapping=(100, 107, 118, 101, 48, 46, 12, 71, 52, 22, 69, 35, 85, 1, 36, 117, 8, 54, 51, 70, 23, 82, 81,
                        88, 25, 34, 44, 109, 97, 74, 16, 37, 38, 73, 28, 79, 57, 62, 112, 61, 24, 83, 78, 6, 20, 56, 94,
                        102, 80, 39, 49, 26, 27, 115, 17, 4, 75, 99, 29, 45, 111, 96, 67, 116, 50, 32, 9, 87, 33, 84, 3,
                        104, 103, 108, 0, 77, 114, 2, 98, 65, 10, 15, 63, 59, 43, 55, 90, 89, 11, 76, 31, 13, 64, 7, 14,
                        47, 92, 105, 21, 113, 72, 110, 19, 30, 5, 93, 60, 42, 91, 18, 66, 53, 58, 95, 106, 68, 40, 86,
                        41),
    ),
    _create_test_layout_description(
        seed_number=50000,
        configuration=LayoutConfiguration(logic=LayoutLogic.NO_GLITCHES,
                                          mode=LayoutMode.STANDARD,
                                          sky_temple_keys=LayoutRandomizedFlag.RANDOMIZED,
                                          item_loss=LayoutEnabledFlag.ENABLED,
                                          elevators=LayoutRandomizedFlag.VANILLA,
                                          hundo_guaranteed=LayoutEnabledFlag.DISABLED,
                                          difficulty=LayoutDifficulty.NORMAL,
                                          pickup_quantities={}),
        pickup_mapping=(55, 59, 76, 66, 95, 78, 115, 114, 1, 69, 101, 53, 93, 88, 0, 92, 113, 43, 15, 81, 23, 82, 33,
                        46, 31, 71, 99, 77, 49, 56, 19, 104, 54, 112, 29, 51, 80, 74, 57, 110, 48, 44, 116, 13, 91, 21,
                        37, 3, 38, 86, 105, 45, 52, 27, 102, 22, 85, 62, 96, 75, 117, 94, 118, 107, 6, 18, 10, 9, 109,
                        58, 72, 17, 67, 25, 68, 20, 8, 87, 79, 70, 36, 40, 97, 5, 32, 41, 84, 111, 12, 35, 61, 30, 100,
                        106, 11, 103, 73, 34, 24, 28, 60, 26, 4, 42, 65, 98, 90, 47, 7, 14, 83, 89, 39, 64, 2, 63, 108,
                        16, 50),
    ),
]


@pytest.fixture(params=_test_descriptions)
def layout_description(request):
    yield request.param


def test_compare_generated_with_data(layout_description: LayoutDescription):
    debug._DEBUG_LEVEL = 0
    status_update = MagicMock()

    data = binary_data.decode_default_prime2()
    generated_description = generator.generate_list(
        data,
        layout_description.seed_number,
        layout_description.configuration,
        status_update=status_update)

    assert generated_description.without_solver_path == layout_description


def test_generate_twice(layout_description: LayoutDescription):
    debug._DEBUG_LEVEL = 0
    status_update = MagicMock()

    data = binary_data.decode_default_prime2()
    generated_description = generator.generate_list(
        data,
        layout_description.seed_number,
        layout_description.configuration,
        status_update=status_update)

    assert generated_description == generator.generate_list(data,
                                                            layout_description.seed_number,
                                                            layout_description.configuration,
                                                            status_update=status_update)
