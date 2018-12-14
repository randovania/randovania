import copy
from typing import Iterable, List, Tuple, Callable, Union
from unittest.mock import MagicMock, patch

import pytest

import randovania.resolver.exceptions
from randovania import VERSION
from randovania.game_description import data_reader
from randovania.game_description.default_database import default_prime2_game_description
from randovania.game_description.resources import PickupIndex, PickupEntry, PickupDatabase
from randovania.games.prime import default_data
from randovania.resolver import generator, debug
from randovania.resolver.filler_library import filter_unassigned_pickup_nodes
from randovania.resolver.game_patches import GamePatches
from randovania.resolver.item_pool import calculate_available_pickups
from randovania.resolver.layout_configuration import LayoutConfiguration, LayoutTrickLevel, LayoutRandomizedFlag, \
    LayoutEnabledFlag
from randovania.resolver.layout_description import LayoutDescription


def _create_test_layout_description(
        seed_number: int,
        configuration: LayoutConfiguration,
        pickup_mapping: Iterable[int]):

    pickup_database = data_reader.read_databases(configuration.game_data)[1]
    return LayoutDescription(
        seed_number=seed_number,
        configuration=configuration,
        version=VERSION,
        pickup_assignment={
            PickupIndex(i): pickup_database.original_pickup_mapping[PickupIndex(new_index)]
            for i, new_index in enumerate(pickup_mapping)
        },
        solver_path=())


_test_descriptions = [
    _create_test_layout_description(
        seed_number=1027649936,
        configuration=LayoutConfiguration.from_params(trick_level=LayoutTrickLevel.NO_TRICKS,
                                                      sky_temple_keys=LayoutRandomizedFlag.RANDOMIZED,
                                                      item_loss=LayoutEnabledFlag.ENABLED,
                                                      elevators=LayoutRandomizedFlag.VANILLA,
                                                      pickup_quantities={}),
        pickup_mapping=[2, 2, 46, 4, 2, 2, 2, 116, 2, 44, 112, 8, 0, 13, 114, 17, 2, 82, 115, 2, 8, 8, 37, 23, 117, 2,
                        52, 50, 2, 4, 76, 4, 2, 75, 2, 57, 38, 8, 8, 2, 2, 4, 17, 2, 74, 2, 4, 83, 2, 43, 106, 2, 21,
                        11, 2, 91, 2, 4, 4, 8, 2, 79, 2, 2, 27, 2, 8, 1, 2, 2, 2, 4, 86, 2, 8, 2, 69, 102, 4, 2, 2, 88,
                        4, 15, 19, 2, 100, 2, 2, 2, 2, 53, 2, 2, 7, 2, 4, 2, 2, 2, 2, 39, 59, 24, 109, 45, 118, 17, 4,
                        68, 4, 2, 4, 2, 2, 17, 2, 92, 2],
    ),
    _create_test_layout_description(
        seed_number=50000,
        configuration=LayoutConfiguration.from_params(trick_level=LayoutTrickLevel.NO_TRICKS,
                                                      sky_temple_keys=LayoutRandomizedFlag.RANDOMIZED,
                                                      item_loss=LayoutEnabledFlag.ENABLED,
                                                      elevators=LayoutRandomizedFlag.VANILLA,
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
        configuration=LayoutConfiguration.from_params(trick_level=LayoutTrickLevel.NO_TRICKS,
                                                      sky_temple_keys=LayoutRandomizedFlag.RANDOMIZED,
                                                      item_loss=LayoutEnabledFlag.ENABLED,
                                                      elevators=LayoutRandomizedFlag.VANILLA,
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
        configuration=LayoutConfiguration.from_params(trick_level=LayoutTrickLevel.HYPERMODE,
                                                      sky_temple_keys=LayoutRandomizedFlag.RANDOMIZED,
                                                      item_loss=LayoutEnabledFlag.ENABLED,
                                                      elevators=LayoutRandomizedFlag.VANILLA,
                                                      pickup_quantities={
                                                          "Light Suit": 2,
                                                          "Darkburst": 0
                                                      }),
        pickup_mapping=[8, 15, 2, 4, 112, 109, 23, 2, 102, 44, 4, 2, 2, 17, 86, 91, 2, 8, 7, 4, 52, 8, 8, 38, 45, 2, 4,
                        2, 2, 50, 4, 75, 2, 2, 8, 2, 13, 82, 4, 2, 4, 2, 2, 17, 8, 118, 4, 8, 2, 83, 4, 2, 4, 21, 88, 4,
                        57, 2, 2, 2, 2, 2, 11, 43, 2, 115, 2, 2, 2, 2, 2, 74, 2, 2, 2, 2, 17, 76, 79, 2, 2, 2, 2, 17,
                        24, 2, 68, 4, 114, 106, 53, 1, 2, 69, 39, 4, 2, 2, 24, 2, 37, 2, 92, 46, 2, 0, 117, 116, 2, 2,
                        2, 59, 4, 2, 19, 100, 2, 2, 8]
        ,
    ),
]


@pytest.fixture(params=[_test_descriptions[0], _test_descriptions[-1]], name="layout_description")
def _layout_description(request):
    yield request.param


def test_generate_seed_with_invalid_quantity_configuration():
    # Setup
    status_update = MagicMock()
    data = default_data.decode_default_prime2()

    configuration = LayoutConfiguration.from_params(
        trick_level=LayoutTrickLevel.NO_TRICKS,
        sky_temple_keys=LayoutRandomizedFlag.RANDOMIZED,
        item_loss=LayoutEnabledFlag.ENABLED,
        elevators=LayoutRandomizedFlag.VANILLA,
        pickup_quantities={"Light Suit": 5})

    # Run
    with pytest.raises(randovania.resolver.exceptions.GenerationFailure):
        generator.generate_list(
            data, 50, configuration,
            status_update=status_update)


# @pytest.mark.skip(reason="generating is taking too long")
def test_compare_generated_with_data(benchmark,
                                     layout_description: LayoutDescription,
                                     echoes_pickup_database: PickupDatabase):
    debug._DEBUG_LEVEL = 0
    status_update = MagicMock()

    data = default_data.decode_default_prime2()
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

    indices: List[int] = [None] * echoes_pickup_database.total_pickup_count
    for index, pickup in generated_description.pickup_assignment.items():
        indices[index.index] = echoes_pickup_database.original_index(pickup).index
    print(indices)

    assert generated_description.without_solver_path == layout_description


@pytest.mark.skip(reason="generating is taking too long")
def test_generate_twice():
    debug._DEBUG_LEVEL = 0
    status_update = MagicMock()
    layout_description = _test_descriptions[0]

    data = default_data.decode_default_prime2()
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
    configuration = LayoutConfiguration.from_params(trick_level=LayoutTrickLevel.NO_TRICKS,
                                                    sky_temple_keys=LayoutRandomizedFlag.RANDOMIZED,
                                                    item_loss=LayoutEnabledFlag.DISABLED,
                                                    elevators=LayoutRandomizedFlag.VANILLA,
                                                    pickup_quantities={})

    generated_description = generator.generate_list(
        simple_data,
        10,
        configuration,
        status_update=status_update)


def _create_patches_filler(logic, initial_state,
                           patches: GamePatches,
                           available_pickups: Tuple[PickupEntry, ...], rng, status_update):
    mapping = copy.copy(patches.pickup_assignment)

    i = 0
    for pickup in available_pickups:
        while PickupIndex(i) in mapping:
            i += 1
        mapping[PickupIndex(i)] = pickup
        i += 1

    return mapping


@patch("randovania.resolver.generator.retcon_playthrough_filler", side_effect=_create_patches_filler, autospec=True)
@patch("randovania.resolver.generator.calculate_item_pool", autospec=True)
@patch("randovania.resolver.generator.Random", autospec=True)
def test_create_patches(mock_random: MagicMock,
                        mock_calculate_item_pool: MagicMock,
                        mock_retcon_playthrough_filler: MagicMock,
                        ):
    # Setup
    seed_number: int = MagicMock()
    game = default_prime2_game_description()
    status_update: Union[MagicMock, Callable[[str], None]] = MagicMock()
    configuration = LayoutConfiguration.from_params(trick_level=LayoutTrickLevel.NO_TRICKS,
                                                    sky_temple_keys=LayoutRandomizedFlag.RANDOMIZED,
                                                    item_loss=LayoutEnabledFlag.DISABLED,
                                                    elevators=LayoutRandomizedFlag.VANILLA,
                                                    pickup_quantities={})
    mock_calculate_item_pool.return_value = list(sorted(game.pickup_database.original_pickup_mapping.values()))

    remaining_items = list(mock_calculate_item_pool.return_value)
    progression = calculate_available_pickups(mock_calculate_item_pool.return_value,
                                              {"translator", "major", "energy_tank", "sky_temple_key"}, None)

    expected_result = {}
    for i, pickup in enumerate(progression):
        expected_result[PickupIndex(i)] = pickup
        remaining_items.remove(pickup)

    for pickup_node in filter_unassigned_pickup_nodes(game.all_nodes, expected_result):
        expected_result[pickup_node.pickup_index] = remaining_items.pop()

    # Run
    patches = generator._create_patches(seed_number, configuration, game, status_update)

    # Assert
    mock_random.assert_called_once_with(seed_number)
    mock_calculate_item_pool.assert_called_once_with(configuration, game)
    mock_retcon_playthrough_filler.assert_called_once()
    assert patches.pickup_assignment == expected_result
