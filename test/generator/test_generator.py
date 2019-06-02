from typing import Iterable, Callable, Union
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from randovania import VERSION
from randovania.game_description import data_reader
from randovania.game_description.default_database import default_prime2_game_description
from randovania.game_description.game_patches import GamePatches
from randovania.generator import generator
from randovania.layout.layout_configuration import LayoutConfiguration, LayoutSkyTempleKeyMode
from randovania.layout.layout_description import LayoutDescription
from randovania.layout.patcher_configuration import PatcherConfiguration
from randovania.layout.permalink import Permalink
from randovania.layout.trick_level import LayoutTrickLevel, TrickLevelConfiguration
from randovania.resolver import debug

skip_generation_tests = pytest.mark.skipif(
    pytest.config.option.skip_generation_tests,
    reason="skipped due to --skip-generation-tests")


def _create_test_layout_description(
        configuration: LayoutConfiguration,
        pickup_mapping: Iterable[int],
) -> LayoutDescription:
    """
    Creates a LayoutDescription for the given configuration, with the patches being for the given pickup_mapping
    :param configuration:
    :param pickup_mapping:
    :return:
    """
    game = data_reader.decode_data(configuration.game_data)
    # pickup_database = game.pickup_database
    # FIXME

    return LayoutDescription(
        version=VERSION,
        permalink=Permalink(
            seed_number=0,
            spoiler=True,
            patcher_configuration=PatcherConfiguration.default(),
            layout_configuration=configuration,
        ),
        patches=GamePatches.with_game(game).assign_new_pickups([
            # (PickupIndex(i), pickup_database.original_pickup_mapping[PickupIndex(new_index)])
            # for i, new_index in enumerate(pickup_mapping)
        ]),
        solver_path=())


# TODO: this permalink is impossible for solver: B6gWMhxALWmCI50gIQBs


_unused_test_descriptions = [
    _create_test_layout_description(
        configuration=LayoutConfiguration.default(),
        pickup_mapping=[2, 88, 4, 7, 4, 38, 23, 76, 2, 2, 2, 46, 57, 82, 24, 2, 106, 83, 2, 39, 37, 8, 69, 2, 15, 2, 52,
                        109, 1, 19, 2, 2, 91, 8, 2, 75, 8, 86, 2, 2, 79, 4, 43, 4, 2, 13, 0, 2, 2, 2, 4, 2, 4, 2, 4, 2,
                        74, 2, 2, 116, 2, 2, 2, 2, 2, 2, 2, 2, 68, 50, 2, 4, 21, 2, 2, 2, 112, 4, 45, 4, 8, 4, 17, 4, 2,
                        100, 2, 115, 8, 2, 24, 2, 4, 44, 17, 2, 2, 2, 102, 118, 11, 8, 2, 4, 2, 17, 92, 53, 2, 2, 59,
                        114, 2, 2, 8, 17, 8, 2, 117],
    ),
    _create_test_layout_description(
        configuration=LayoutConfiguration.default(),
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
        configuration=LayoutConfiguration.default(),
        pickup_mapping=[37, 2, 2, 68, 100, 38, 102, 109, 8, 17, 4, 69, 88, 13, 44, 2, 4, 2, 74, 2, 27, 23, 2, 46, 43,
                        15, 2, 2, 50, 4, 24, 2, 2, 2, 2, 57, 2, 2, 2, 4, 4, 115, 2, 53, 7, 2, 2, 59, 75, 8, 2, 52, 8, 2,
                        19, 112, 2, 8, 17, 92, 2, 2, 79, 106, 2, 4, 2, 17, 4, 2, 2, 2, 2, 117, 2, 2, 2, 17, 2, 8, 82, 8,
                        2, 4, 114, 118, 2, 91, 8, 4, 4, 11, 2, 2, 4, 1, 2, 0, 4, 8, 2, 116, 2, 4, 2, 2, 86, 2, 2, 39, 2,
                        21, 2, 2, 45, 2, 4, 76, 83]

        ,
    ),
    _create_test_layout_description(
        configuration=LayoutConfiguration.from_params(
            trick_level_configuration=TrickLevelConfiguration(LayoutTrickLevel.HYPERMODE),
        ),
        pickup_mapping=[91, 45, 17, 24, 4, 2, 23, 59, 2, 0, 2, 68, 8, 38, 2, 2, 2, 7, 4, 115, 37, 2, 86, 2, 76, 2, 4, 2,
                        117, 112, 17, 2, 2, 2, 13, 39, 88, 82, 102, 50, 57, 2, 52, 116, 2, 4, 2, 8, 118, 2, 2, 2, 1, 2,
                        2, 53, 74, 2, 2, 114, 4, 2, 4, 8, 2, 8, 2, 2, 19, 2, 43, 2, 2, 2, 2, 2, 2, 8, 4, 2, 2, 2, 4,
                        109, 2, 4, 2, 4, 11, 8, 69, 92, 2, 4, 106, 17, 17, 21, 75, 79, 2, 2, 2, 100, 2, 15, 83, 8, 4, 2,
                        2, 46, 24, 2, 4, 44, 8, 4, 2]

        ,
    ),
    _create_test_layout_description(
        configuration=LayoutConfiguration.from_params(
            trick_level_configuration=TrickLevelConfiguration(LayoutTrickLevel.MINIMAL_RESTRICTIONS),
            sky_temple_keys=LayoutSkyTempleKeyMode.ALL_BOSSES,
        ),
        pickup_mapping=[8, 2, 4, 2, 21, 2, 38, 115, 2, 2, 86, 2, 2, 2, 8, 109, 76, 44, 100, 2, 8, 2, 4, 8, 2, 116, 2,
                        69, 2, 57, 2, 4, 2, 4, 8, 17, 2, 11, 117, 8, 39, 2, 2, 53, 27, 2, 2, 59, 2, 2, 79, 4, 24, 2, 2,
                        4, 46, 17, 4, 2, 1, 17, 74, 8, 2, 4, 43, 17, 13, 2, 118, 88, 4, 2, 2, 15, 2, 2, 8, 45, 112, 2,
                        4, 92, 4, 2, 19, 2, 91, 2, 75, 2, 4, 2, 50, 114, 7, 23, 2, 37, 2, 2, 68, 102, 2, 2, 2, 2, 2, 0,
                        2, 52, 4, 82, 2, 106, 2, 4, 83]

        ,
    ),
]


@skip_generation_tests
@pytest.mark.skip
@pytest.mark.parametrize("layout_description", _test_descriptions)
@patch("randovania.layout.permalink.Permalink.as_str", new_callable=PropertyMock)
def test_compare_generated_with_data(mock_permalink_as_str: PropertyMock,
                                     layout_description: LayoutDescription):
    debug._DEBUG_LEVEL = 0
    status_update = MagicMock()
    mock_permalink_as_str.return_value = "fixed-seed!"

    generated_description = generator.generate_description(
        layout_description.permalink, status_update=status_update, validate_after_generation=True, timeout=None)

    # indices: List[int] = [None] * echoes_pickup_database.total_pickup_count
    # for index, pickup in generated_description.patches.pickup_assignment.items():
    #     indices[index.index] = echoes_pickup_database.original_index(pickup).index
    # print(indices)

    assert generated_description.without_solver_path == layout_description


@patch("randovania.generator.generator._assign_remaining_items", autospec=True)
@patch("randovania.generator.generator.run_filler", autospec=True)
@patch("randovania.generator.generator._validate_item_pool_size", autospec=True)
@patch("randovania.generator.base_patches_factory.create_base_patches", autospec=True)
@patch("randovania.generator.item_pool.pool_creator.calculate_item_pool", autospec=True)
@patch("randovania.generator.generator.Random", autospec=False)  # TODO: pytest-qt bug
def test_create_patches(mock_random: MagicMock,
                        mock_calculate_item_pool: MagicMock,
                        mock_create_base_patches: MagicMock,
                        mock_validate_item_pool_size: MagicMock,
                        mock_run_filler: MagicMock,
                        mock_assign_remaining_items: MagicMock,
                        ):
    # Setup
    game = default_prime2_game_description()
    status_update: Union[MagicMock, Callable[[str], None]] = MagicMock()

    permalink = MagicMock()
    pool_patches = MagicMock()
    item_pool = MagicMock()
    filler_patches = MagicMock()
    remaining_items = MagicMock()

    mock_calculate_item_pool.return_value = pool_patches, item_pool
    mock_run_filler.return_value = filler_patches, remaining_items

    # Run
    result = generator._create_randomized_patches(permalink, game, status_update)

    # Assert
    mock_random.assert_called_once_with(permalink.as_str)
    mock_create_base_patches.assert_called_once_with(permalink.layout_configuration, mock_random.return_value, game)

    # pool
    mock_calculate_item_pool.assert_called_once_with(permalink.layout_configuration,
                                                     game.resource_database,
                                                     mock_create_base_patches.return_value)

    mock_validate_item_pool_size.assert_called_once_with(item_pool, game)
    mock_run_filler.assert_called_once_with(
        permalink.layout_configuration, game, item_pool, pool_patches, mock_random.return_value, status_update
    )
    mock_assign_remaining_items.assert_called_once_with(
        mock_random.return_value, game.world_list, filler_patches.pickup_assignment, remaining_items
    )
    filler_patches.assign_pickup_assignment.assert_called_once_with(mock_assign_remaining_items.return_value)

    assert result == filler_patches.assign_pickup_assignment.return_value
