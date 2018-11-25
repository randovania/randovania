from typing import Iterable, List
from unittest.mock import MagicMock

import pytest

import randovania.resolver.exceptions
from randovania import VERSION
from randovania.game_description.resources import PickupIndex
from randovania.games.prime import binary_data
from randovania.interface_common.echoes import default_prime2_pickup_database
from randovania.resolver import generator, debug
from randovania.resolver.layout_configuration import LayoutConfiguration, LayoutLogic, LayoutMode, LayoutRandomizedFlag, \
    LayoutEnabledFlag, LayoutDifficulty
from randovania.resolver.layout_description import LayoutDescription


def _create_test_layout_description(
        seed_number: int,
        configuration: LayoutConfiguration,
        pickup_mapping: Iterable[int]):
    pickup_database = default_prime2_pickup_database()
    return LayoutDescription(
        seed_number=seed_number,
        configuration=configuration,
        version=VERSION,
        pickup_assignment=pickup_database.original_pickup_mapping,
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
        pickup_mapping=[0, 0, 7, 39, 115, 0, 0, 0, 0, 38, 79, 0, 0, 13, 27, 0, 46, 117, 109, 0, 8, 23, 37, 44, 15, 100,
                        17, 0, 0, 86, 0, 88, 59, 50, 0, 112, 4, 74, 43, 0, 0, 52, 19, 0, 4, 8, 8, 75, 57, 0, 0, 0, 0, 0,
                        0, 4, 17, 24, 0, 0, 76, 102, 0, 0, 116, 9, 8, 4, 4, 11, 0, 0, 0, 118, 69, 0, 0, 0, 0, 4, 0, 8,
                        92, 1, 17, 0, 8, 83, 4, 68, 8, 0, 0, 0, 0, 0, 106, 0, 0, 0, 114, 4, 0, 21, 0, 4, 4, 53, 4, 0, 4,
                        4, 0, 17, 45, 82, 0, 8, 91],
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
                                              "Sky Temple Key 1": 2,
                                              "Darkburst": 0
                                          }),
        pickup_mapping=(108, 90, 1, 58, 48, 101, 20, 12, 38, 2, 100, 4, 6, 88, 39, 70, 33, 93, 115, 3, 23, 82, 60, 46,
                        110, 105, 102, 67, 41, 77, 65, 37, 8, 118, 30, 24, 36, 74, 81, 53, 99, 69, 61, 26, 73, 59, 52,
                        45, 87, 76, 0, 42, 78, 5, 44, 79, 86, 57, 89, 94, 68, 71, 13, 14, 97, 83, 98, 62, 80, 40, 116,
                        28, 107, 96, 21, 45, 64, 103, 84, 19, 31, 113, 56, 55, 104, 109, 95, 10, 92, 91, 51, 34, 22,
                        25, 17, 9, 18, 50, 32, 47, 11, 85, 49, 43, 114, 35, 29, 111, 15, 63, 72, 7, 112, 75, 106, 66,
                        16, 54, 117),
    ),
]


@pytest.fixture(params=[_test_descriptions[0]], name="layout_description")
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
    with pytest.raises(randovania.resolver.exceptions.GenerationFailure):
        generator.generate_list(
            data, 50, configuration,
            status_update=status_update)


# @pytest.mark.skip(reason="generating is taking too long")
def test_compare_generated_with_data(benchmark, layout_description: LayoutDescription):
    debug._DEBUG_LEVEL = 0
    status_update = MagicMock()

    data = binary_data.decode_default_prime2()
    generated_description: LayoutDescription = benchmark.pedantic(
        generator.generate_list,
        args=(
            data,
            layout_description.seed_number,
            layout_description.configuration,
        ),
        kwargs={
            'status_update': status_update
        },
        iterations=1,
        rounds=1)

    pickup_database = default_prime2_pickup_database()
    indices: List[int] = [None] * pickup_database.total_pickup_count
    for index, pickup in generated_description.pickup_assignment.items():
        indices[index.index] = pickup_database.original_index(pickup).index
    print(indices)

    assert generated_description.without_solver_path == layout_description


@pytest.mark.skip(reason="generating is taking too long")
def test_generate_twice():
    debug._DEBUG_LEVEL = 0
    status_update = MagicMock()
    layout_description = _test_descriptions[0]

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


@pytest.mark.skip(reason="simple data is broken")
def test_generate_simple(simple_data: dict):
    status_update = MagicMock()
    configuration = LayoutConfiguration(logic=LayoutLogic.NO_GLITCHES,
                                        mode=LayoutMode.STANDARD,
                                        sky_temple_keys=LayoutRandomizedFlag.RANDOMIZED,
                                        item_loss=LayoutEnabledFlag.DISABLED,
                                        elevators=LayoutRandomizedFlag.VANILLA,
                                        hundo_guaranteed=LayoutEnabledFlag.DISABLED,
                                        difficulty=LayoutDifficulty.NORMAL,
                                        pickup_quantities={})

    generated_description = generator.generate_list(
        simple_data,
        10,
        configuration,
        status_update=status_update)
