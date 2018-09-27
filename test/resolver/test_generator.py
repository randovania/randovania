from unittest.mock import MagicMock

import pytest

from randovania import VERSION
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
        version=VERSION,
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
                                          difficulty=LayoutDifficulty.NORMAL,
                                          pickup_quantities={}),
        pickup_mapping=(100, 90, 118, 73, 95, 46, 25, 17, 52, 32, 69, 101, 80, 1, 103, 117, 31, 107, 97, 10, 23, 82, 67,
                        88, 54, 110, 44, 109, 61, 74, 26, 37, 38, 6, 28, 79, 57, 8, 112, 12, 24, 83, 3, 30, 51, 96, 78,
                        102, 4, 39, 94, 58, 27, 115, 36, 34, 75, 70, 47, 45, 87, 66, 18, 116, 50, 20, 49, 63, 22, 65,
                        48, 71, 60, 89, 56, 5, 114, 40, 72, 0, 33, 15, 16, 59, 43, 113, 64, 84, 11, 76, 21, 13, 14, 7,
                        29, 99, 92, 85, 42, 93, 9, 77, 19, 41, 55, 81, 108, 111, 91, 35, 2, 53, 105, 62, 106, 68, 98,
                        86, 104),
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
        pickup_mapping=(113, 59, 76, 2, 62, 3, 115, 114, 1, 69, 73, 53, 81, 88, 56, 92, 93, 43, 15, 67, 23, 82, 22, 46,
                        21, 17, 70, 5, 94, 96, 19, 71, 107, 112, 47, 97, 4, 74, 57, 77, 95, 44, 116, 13, 91, 42, 37, 48,
                        38, 86, 85, 45, 52, 27, 102, 32, 80, 8, 66, 75, 117, 78, 118, 90, 30, 35, 33, 49, 109, 105, 9,
                        36, 18, 54, 68, 51, 31, 63, 79, 10, 103, 98, 61, 55, 20, 104, 65, 87, 25, 101, 12, 41, 100, 106,
                        11, 60, 6, 110, 24, 28, 108, 58, 34, 111, 0, 72, 64, 99, 7, 29, 83, 84, 39, 14, 40, 16, 89, 26,
                        50),
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
                                          pickup_quantities={
                                              "Missile Expansion": 0
                                          }),
        pickup_mapping=(21, 59, 76, 21, 108, 21, 115, 114, 1, 69, 4, 53, 96, 88, 56, 92, 90, 43, 15, 21, 23, 82, 21, 46,
                        21, 21, 9, 21, 21, 21, 19, 80, 21, 112, 21, 21, 21, 74, 57, 70, 21, 44, 116, 13, 91, 21, 37, 55,
                        38, 86, 64, 45, 52, 27, 102, 21, 21, 21, 8, 75, 117, 105, 118, 78, 26, 21, 21, 21, 109, 21, 21,
                        21, 21, 21, 68, 21, 42, 111, 79, 21, 21, 21, 16, 25, 21, 21, 21, 71, 21, 21, 21, 21, 100, 106,
                        11, 65, 21, 21, 24, 21, 21, 21, 33, 21, 21, 17, 94, 21, 7, 21, 83, 95, 39, 21, 40, 21, 72, 21,
                        50),
    ),
]


@pytest.fixture(params=_test_descriptions, name="layout_description")
def _layout_description(request):
    yield request.param


def test_generate_seed_with_invalid_quantity_configuration():
    # Setup
    status_update = MagicMock()
    data = binary_data.decode_default_prime2()

    configuration = LayoutConfiguration(
        logic=LayoutLogic.NO_GLITCHES,
        mode=LayoutMode.STANDARD,
        sky_temple_keys=LayoutRandomizedFlag.RANDOMIZED,
        item_loss=LayoutEnabledFlag.ENABLED,
        elevators=LayoutRandomizedFlag.VANILLA,
        hundo_guaranteed=LayoutEnabledFlag.DISABLED,
        difficulty=LayoutDifficulty.NORMAL,
        pickup_quantities={"Undefined Item": 5})

    # Run
    with pytest.raises(generator.GenerationFailure):
        generator.generate_list(
            data, 50, configuration,
            status_update=status_update)


def test_compare_generated_with_data(layout_description: LayoutDescription):
    debug._DEBUG_LEVEL = 0
    status_update = MagicMock()

    data = binary_data.decode_default_prime2()
    generated_description = generator.generate_list(
        data,
        layout_description.seed_number,
        layout_description.configuration,
        status_update=status_update)

    print(generated_description.pickup_mapping)
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
