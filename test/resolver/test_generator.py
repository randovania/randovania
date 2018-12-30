import copy
from typing import Iterable, List, Tuple, Callable, Union
from unittest.mock import MagicMock, patch

import pytest

import randovania.resolver.exceptions
from randovania import VERSION
from randovania.game_description import data_reader
from randovania.game_description.default_database import default_prime2_game_description
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resources import PickupIndex, PickupEntry, PickupDatabase
from randovania.resolver import generator, debug
from randovania.resolver.filler_library import filter_unassigned_pickup_nodes
from randovania.resolver.item_pool import calculate_available_pickups
from randovania.resolver.layout_configuration import LayoutConfiguration, LayoutTrickLevel, LayoutRandomizedFlag, \
    LayoutEnabledFlag, LayoutSkyTempleKeyMode
from randovania.resolver.layout_description import LayoutDescription
from randovania.resolver.patcher_configuration import PatcherConfiguration
from randovania.resolver.permalink import Permalink


def _create_test_layout_description(
        seed_number: int,
        configuration: LayoutConfiguration,
        pickup_mapping: Iterable[int]):
    pickup_database = data_reader.read_databases(configuration.game_data)[1]
    return LayoutDescription(
        version=VERSION,
        permalink=Permalink(
            seed_number=seed_number,
            spoiler=True,
            patcher_configuration=PatcherConfiguration.default(),
            layout_configuration=configuration,
        ),
        patches=GamePatches(
            {
                PickupIndex(i): pickup_database.original_pickup_mapping[PickupIndex(new_index)]
                for i, new_index in enumerate(pickup_mapping)
            },
            {}, {}, {}
        ),
        solver_path=())


# TODO: this permalink is impossible for solver: B6gWMhxALWmCI50gIQBs


_unused_test_descriptions = [
    _create_test_layout_description(
        seed_number=50000,
        configuration=LayoutConfiguration.from_params(trick_level=LayoutTrickLevel.NO_TRICKS,
                                                      sky_temple_keys=LayoutSkyTempleKeyMode.FULLY_RANDOM,
                                                      item_loss=LayoutEnabledFlag.ENABLED,
                                                      elevators=LayoutRandomizedFlag.VANILLA,
                                                      pickup_quantities={}),
        pickup_mapping=[2, 88, 4, 7, 4, 38, 23, 76, 2, 2, 2, 46, 57, 82, 24, 2, 106, 83, 2, 39, 37, 8, 69, 2, 15, 2, 52,
                        109, 1, 19, 2, 2, 91, 8, 2, 75, 8, 86, 2, 2, 79, 4, 43, 4, 2, 13, 0, 2, 2, 2, 4, 2, 4, 2, 4, 2,
                        74, 2, 2, 116, 2, 2, 2, 2, 2, 2, 2, 2, 68, 50, 2, 4, 21, 2, 2, 2, 112, 4, 45, 4, 8, 4, 17, 4, 2,
                        100, 2, 115, 8, 2, 24, 2, 4, 44, 17, 2, 2, 2, 102, 118, 11, 8, 2, 4, 2, 17, 92, 53, 2, 2, 59,
                        114, 2, 2, 8, 17, 8, 2, 117],
    ),
    _create_test_layout_description(
        seed_number=50000,
        configuration=LayoutConfiguration.from_params(trick_level=LayoutTrickLevel.NO_TRICKS,
                                                      sky_temple_keys=LayoutSkyTempleKeyMode.FULLY_RANDOM,
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
]

_test_descriptions = [
    _create_test_layout_description(
        seed_number=1027649986,
        configuration=LayoutConfiguration.from_params(trick_level=LayoutTrickLevel.NO_TRICKS,
                                                      sky_temple_keys=LayoutSkyTempleKeyMode.FULLY_RANDOM,
                                                      item_loss=LayoutEnabledFlag.ENABLED,
                                                      elevators=LayoutRandomizedFlag.VANILLA,
                                                      pickup_quantities={}),
        pickup_mapping=[2, 2, 52, 115, 46, 2, 13, 4, 43, 38, 2, 2, 4, 1, 106, 50, 37, 2, 2, 117, 69, 2, 0, 23, 86, 4, 2,
                        44, 88, 2, 2, 8, 91, 8, 74, 82, 8, 4, 39, 2, 76, 2, 4, 2, 4, 8, 57, 24, 4, 2, 2, 2, 4, 53, 75,
                        2, 2, 2, 2, 2, 17, 2, 2, 92, 2, 114, 2, 2, 2, 45, 4, 116, 102, 21, 8, 2, 2, 8, 4, 2, 2, 2, 109,
                        112, 15, 8, 2, 2, 2, 68, 2, 17, 2, 2, 2, 118, 17, 2, 2, 2, 4, 2, 79, 100, 11, 8, 2, 27, 4, 83,
                        59, 4, 4, 2, 7, 19, 17, 2, 2],
    ),
    _create_test_layout_description(
        seed_number=50000,
        configuration=LayoutConfiguration.from_params(trick_level=LayoutTrickLevel.HYPERMODE,
                                                      sky_temple_keys=LayoutSkyTempleKeyMode.FULLY_RANDOM,
                                                      item_loss=LayoutEnabledFlag.ENABLED,
                                                      elevators=LayoutRandomizedFlag.VANILLA,
                                                      pickup_quantities={
                                                          "Light Suit": 2,
                                                          "Darkburst": 0
                                                      }),
        pickup_mapping=[2, 52, 46, 116, 38, 4, 88, 2, 100, 2, 2, 2, 82, 23, 8, 2, 114, 86, 2, 4, 2, 13, 37, 4, 2, 4, 8,
                        2, 2, 4, 2, 7, 8, 2, 2, 75, 2, 4, 8, 2, 83, 43, 2, 21, 2, 2, 57, 4, 2, 76, 24, 39, 8, 115, 2, 2,
                        2, 109, 117, 8, 74, 2, 68, 59, 2, 15, 4, 4, 50, 2, 2, 4, 112, 2, 2, 11, 2, 45, 2, 2, 4, 2, 2, 2,
                        102, 53, 2, 91, 79, 2, 19, 17, 2, 8, 4, 2, 2, 106, 2, 4, 2, 24, 92, 2, 2, 8, 69, 0, 4, 17, 2, 1,
                        2, 2, 44, 17, 2, 17, 118]
        ,
    ),
]


@pytest.fixture(params=_test_descriptions, name="layout_description")
def _layout_description(request):
    yield request.param


def test_generate_seed_with_invalid_quantity_configuration():
    # Setup
    status_update = MagicMock()

    configuration = LayoutConfiguration.from_params(
        trick_level=LayoutTrickLevel.NO_TRICKS,
        sky_temple_keys=LayoutSkyTempleKeyMode.FULLY_RANDOM,
        item_loss=LayoutEnabledFlag.ENABLED,
        elevators=LayoutRandomizedFlag.VANILLA,
        pickup_quantities={"Light Suit": 5})

    permalink = Permalink(
        seed_number=50,
        spoiler=True,
        patcher_configuration=PatcherConfiguration.default(),
        layout_configuration=configuration,
    )

    # Run
    with pytest.raises(randovania.resolver.exceptions.GenerationFailure):
        generator.generate_list(permalink, status_update=status_update)


# @pytest.mark.skip(reason="generating is taking too long")
def test_compare_generated_with_data(benchmark,
                                     layout_description: LayoutDescription,
                                     echoes_pickup_database: PickupDatabase):
    debug._DEBUG_LEVEL = 0
    status_update = MagicMock()

    generated_description: LayoutDescription = benchmark.pedantic(
        generator.generate_list,
        args=(
            layout_description.permalink,
        ),
        kwargs={
            'status_update': status_update
        },
        iterations=1,
        rounds=1)

    indices: List[int] = [None] * echoes_pickup_database.total_pickup_count
    for index, pickup in generated_description.patches.pickup_assignment.items():
        indices[index.index] = echoes_pickup_database.original_index(pickup).index
    print(indices)

    assert generated_description.without_solver_path == layout_description


@pytest.mark.skip(reason="generating is taking too long")
def test_generate_twice():
    debug._DEBUG_LEVEL = 0
    status_update = MagicMock()
    layout_description = _test_descriptions[0]

    generated_description = generator.generate_list(layout_description.permalink, status_update)
    assert generated_description == generator.generate_list(layout_description.permalink, status_update)


@pytest.mark.skip(reason="simple data is broken")
def test_generate_simple(simple_data: dict):
    status_update = MagicMock()
    configuration = LayoutConfiguration.from_params(trick_level=LayoutTrickLevel.NO_TRICKS,
                                                    sky_temple_keys=LayoutRandomizedFlag.RANDOMIZED,
                                                    item_loss=LayoutEnabledFlag.DISABLED,
                                                    elevators=LayoutRandomizedFlag.VANILLA,
                                                    pickup_quantities={})

    generated_description = generator.generate_list(configuration, status_update)


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
    seed_number: int = 91319
    game = default_prime2_game_description()
    status_update: Union[MagicMock, Callable[[str], None]] = MagicMock()
    configuration = LayoutConfiguration.from_params(trick_level=LayoutTrickLevel.NO_TRICKS,
                                                    sky_temple_keys=LayoutSkyTempleKeyMode.FULLY_RANDOM,
                                                    item_loss=LayoutEnabledFlag.DISABLED,
                                                    elevators=LayoutRandomizedFlag.VANILLA,
                                                    pickup_quantities={})
    permalink = Permalink(
        seed_number=seed_number,
        spoiler=True,
        patcher_configuration=PatcherConfiguration.default(),
        layout_configuration=configuration,
    )
    mock_calculate_item_pool.return_value = list(sorted(game.pickup_database.original_pickup_mapping.values()))

    remaining_items = list(mock_calculate_item_pool.return_value)
    progression = calculate_available_pickups(mock_calculate_item_pool.return_value,
                                              {"translator", "major", "energy_tank", "sky_temple_key"}, None)

    expected_result = {}
    for i, pickup in enumerate(progression):
        expected_result[PickupIndex(i)] = pickup
        remaining_items.remove(pickup)

    for pickup_node in filter_unassigned_pickup_nodes(game.world_list.all_nodes, expected_result):
        expected_result[pickup_node.pickup_index] = remaining_items.pop()

    # Run
    patches = generator._create_patches(permalink, game, status_update)

    # Assert
    mock_random.assert_called_once_with(permalink.as_str)
    mock_calculate_item_pool.assert_called_once_with(permalink, game)
    mock_retcon_playthrough_filler.assert_called_once()
    assert patches.pickup_assignment == expected_result
