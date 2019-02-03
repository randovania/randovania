from typing import Iterable, List, Callable, Union
from unittest.mock import MagicMock, patch, PropertyMock, ANY

import pytest

import randovania.resolver.exceptions
from randovania import VERSION
from randovania.game_description import data_reader
from randovania.game_description.default_database import default_prime2_game_description
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resources import PickupIndex, PickupEntry, PickupDatabase
from randovania.layout.layout_configuration import LayoutConfiguration, LayoutTrickLevel, LayoutRandomizedFlag, \
    LayoutSkyTempleKeyMode
from randovania.layout.layout_description import LayoutDescription
from randovania.layout.patcher_configuration import PatcherConfiguration
from randovania.layout.permalink import Permalink
from randovania.layout.starting_location import StartingLocation
from randovania.layout.starting_resources import StartingResources
from randovania.resolver import generator, debug
from randovania.resolver.exceptions import GenerationFailure

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
    pickup_database = game.pickup_database

    return LayoutDescription(
        version=VERSION,
        permalink=Permalink(
            seed_number=0,
            spoiler=True,
            patcher_configuration=PatcherConfiguration.default(),
            layout_configuration=configuration,
        ),
        patches=GamePatches.with_game(game).assign_new_pickups([
            (PickupIndex(i), pickup_database.original_pickup_mapping[PickupIndex(new_index)])
            for i, new_index in enumerate(pickup_mapping)
        ]),
        solver_path=())


# TODO: this permalink is impossible for solver: B6gWMhxALWmCI50gIQBs


_unused_test_descriptions = [
    _create_test_layout_description(
        configuration=LayoutConfiguration.from_params(trick_level=LayoutTrickLevel.NO_TRICKS,
                                                      sky_temple_keys=LayoutSkyTempleKeyMode.FULLY_RANDOM,
                                                      elevators=LayoutRandomizedFlag.VANILLA,
                                                      pickup_quantities={},
                                                      starting_location=StartingLocation.default(),
                                                      starting_resources=StartingResources.default(),
                                                      ),
        pickup_mapping=[2, 88, 4, 7, 4, 38, 23, 76, 2, 2, 2, 46, 57, 82, 24, 2, 106, 83, 2, 39, 37, 8, 69, 2, 15, 2, 52,
                        109, 1, 19, 2, 2, 91, 8, 2, 75, 8, 86, 2, 2, 79, 4, 43, 4, 2, 13, 0, 2, 2, 2, 4, 2, 4, 2, 4, 2,
                        74, 2, 2, 116, 2, 2, 2, 2, 2, 2, 2, 2, 68, 50, 2, 4, 21, 2, 2, 2, 112, 4, 45, 4, 8, 4, 17, 4, 2,
                        100, 2, 115, 8, 2, 24, 2, 4, 44, 17, 2, 2, 2, 102, 118, 11, 8, 2, 4, 2, 17, 92, 53, 2, 2, 59,
                        114, 2, 2, 8, 17, 8, 2, 117],
    ),
    _create_test_layout_description(
        configuration=LayoutConfiguration.from_params(trick_level=LayoutTrickLevel.NO_TRICKS,
                                                      sky_temple_keys=LayoutSkyTempleKeyMode.FULLY_RANDOM,
                                                      elevators=LayoutRandomizedFlag.VANILLA,
                                                      pickup_quantities={
                                                          "Missile Expansion": 0
                                                      },
                                                      starting_location=StartingLocation.default(),
                                                      starting_resources=StartingResources.default(),
                                                      ),
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
        configuration=LayoutConfiguration.from_params(trick_level=LayoutTrickLevel.NO_TRICKS,
                                                      sky_temple_keys=LayoutSkyTempleKeyMode.FULLY_RANDOM,
                                                      elevators=LayoutRandomizedFlag.VANILLA,
                                                      pickup_quantities={},
                                                      starting_location=StartingLocation.default(),
                                                      starting_resources=StartingResources.default(),
                                                      ),
        pickup_mapping=[37, 2, 2, 68, 100, 38, 102, 109, 8, 17, 4, 69, 88, 13, 44, 2, 4, 2, 74, 2, 27, 23, 2, 46, 43,
                        15, 2, 2, 50, 4, 24, 2, 2, 2, 2, 57, 2, 2, 2, 4, 4, 115, 2, 53, 7, 2, 2, 59, 75, 8, 2, 52, 8, 2,
                        19, 112, 2, 8, 17, 92, 2, 2, 79, 106, 2, 4, 2, 17, 4, 2, 2, 2, 2, 117, 2, 2, 2, 17, 2, 8, 82, 8,
                        2, 4, 114, 118, 2, 91, 8, 4, 4, 11, 2, 2, 4, 1, 2, 0, 4, 8, 2, 116, 2, 4, 2, 2, 86, 2, 2, 39, 2,
                        21, 2, 2, 45, 2, 4, 76, 83]

        ,
    ),
    _create_test_layout_description(
        configuration=LayoutConfiguration.from_params(trick_level=LayoutTrickLevel.HYPERMODE,
                                                      sky_temple_keys=LayoutSkyTempleKeyMode.FULLY_RANDOM,
                                                      elevators=LayoutRandomizedFlag.VANILLA,
                                                      pickup_quantities={
                                                          "Light Suit": 2,
                                                          "Darkburst": 0
                                                      },
                                                      starting_location=StartingLocation.default(),
                                                      starting_resources=StartingResources.default(),
                                                      ),
        pickup_mapping=[46, 45, 2, 24, 4, 2, 23, 2, 2, 2, 8, 68, 2, 38, 117, 2, 2, 7, 2, 115, 37, 4, 2, 2, 2, 8, 2, 8,
                        2, 112, 2, 8, 4, 86, 13, 69, 88, 82, 102, 50, 57, 8, 52, 2, 118, 4, 17, 2, 21, 2, 2, 2, 1, 2, 2,
                        53, 74, 17, 2, 2, 2, 2, 4, 2, 92, 8, 4, 2, 19, 2, 43, 2, 2, 2, 8, 2, 2, 116, 2, 8, 2, 2, 59, 44,
                        2, 2, 76, 114, 11, 4, 2, 100, 2, 2, 106, 4, 2, 24, 75, 79, 4, 17, 4, 4, 17, 15, 2, 2, 109, 2, 2,
                        91, 4, 0, 4, 39, 83, 2, 4]

        ,
    ),
    _create_test_layout_description(
        configuration=LayoutConfiguration.from_params(trick_level=LayoutTrickLevel.MINIMAL_RESTRICTIONS,
                                                      sky_temple_keys=LayoutSkyTempleKeyMode.ALL_BOSSES,
                                                      elevators=LayoutRandomizedFlag.VANILLA,
                                                      pickup_quantities={},
                                                      starting_location=StartingLocation.default(),
                                                      starting_resources=StartingResources.default(),
                                                      ),
        pickup_mapping=[8, 2, 4, 2, 21, 2, 38, 115, 2, 2, 86, 2, 2, 2, 8, 109, 76, 44, 100, 2, 8, 2, 4, 8, 2, 116, 2,
                        69, 2, 57, 2, 4, 2, 4, 8, 17, 2, 11, 117, 8, 39, 2, 2, 53, 27, 2, 2, 59, 2, 2, 79, 4, 24, 2, 2,
                        4, 46, 17, 4, 2, 1, 17, 74, 8, 2, 4, 43, 17, 13, 2, 118, 88, 4, 2, 2, 15, 2, 2, 8, 45, 112, 2,
                        4, 92, 4, 2, 19, 2, 91, 2, 75, 2, 4, 2, 50, 114, 7, 23, 2, 37, 2, 2, 68, 102, 2, 2, 2, 2, 2, 0,
                        2, 52, 4, 82, 2, 106, 2, 4, 83]

        ,
    ),
]


def test_generate_seed_with_invalid_quantity_configuration():
    # Setup
    status_update = MagicMock()

    configuration = LayoutConfiguration.from_params(
        trick_level=LayoutTrickLevel.NO_TRICKS,
        sky_temple_keys=LayoutSkyTempleKeyMode.FULLY_RANDOM,
        elevators=LayoutRandomizedFlag.VANILLA,
        pickup_quantities={"Light Suit": 5},
        starting_location=StartingLocation.default(),
        starting_resources=StartingResources.default(),
    )

    permalink = Permalink(
        seed_number=50,
        spoiler=True,
        patcher_configuration=PatcherConfiguration.default(),
        layout_configuration=configuration,
    )

    # Run
    with pytest.raises(randovania.resolver.exceptions.GenerationFailure):
        generator.generate_list(permalink, status_update=status_update)


@skip_generation_tests
@pytest.mark.parametrize("layout_description", _test_descriptions)
@patch("randovania.layout.permalink.Permalink.as_str", new_callable=PropertyMock)
def test_compare_generated_with_data(mock_permalink_as_str: PropertyMock,
                                     layout_description: LayoutDescription,
                                     echoes_pickup_database: PickupDatabase):
    debug._DEBUG_LEVEL = 0
    status_update = MagicMock()
    mock_permalink_as_str.return_value = "fixed-seed!"

    generated_description = generator.generate_list(
        layout_description.permalink, status_update=status_update, timeout=None)

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


@patch("randovania.resolver.generator._indices_for_unassigned_pickups", autospec=True)
@patch("randovania.resolver.generator.retcon_playthrough_filler", autospec=True)
@patch("randovania.resolver.generator._sky_temple_key_distribution_logic", autospec=True)
@patch("randovania.resolver.generator.calculate_item_pool", autospec=True)
@patch("randovania.resolver.generator.Random", autospec=True)
def test_create_patches(mock_random: MagicMock,
                        mock_calculate_item_pool: MagicMock,
                        mock_sky_temple_key_distribution_logic: MagicMock,
                        mock_retcon_playthrough_filler: MagicMock,
                        mock_indices_for_unassigned_pickups: MagicMock,
                        ):
    # Setup
    seed_number: int = 91319
    game = default_prime2_game_description()
    status_update: Union[MagicMock, Callable[[str], None]] = MagicMock()
    configuration = LayoutConfiguration.from_params(trick_level=LayoutTrickLevel.NO_TRICKS,
                                                    sky_temple_keys=LayoutSkyTempleKeyMode.FULLY_RANDOM,
                                                    elevators=LayoutRandomizedFlag.VANILLA,
                                                    pickup_quantities={},
                                                    starting_location=StartingLocation.default(),
                                                    starting_resources=StartingResources.from_item_loss(False),
                                                    )
    permalink = Permalink(
        seed_number=seed_number,
        spoiler=True,
        patcher_configuration=PatcherConfiguration.default(),
        layout_configuration=configuration,
    )
    mock_calculate_item_pool.return_value = list(sorted(game.pickup_database.original_pickup_mapping.values()))
    mock_sky_temple_key_distribution_logic.return_value.starting_location = game.starting_location
    mock_sky_temple_key_distribution_logic.return_value.custom_initial_items = None

    filler_patches = mock_retcon_playthrough_filler.return_value

    # Run
    result = generator._create_patches(permalink, game, status_update)

    # Assert
    mock_random.assert_called_once_with(permalink.as_str)
    mock_calculate_item_pool.assert_called_once_with(permalink, game)

    mock_sky_temple_key_distribution_logic.assert_called_once_with(permalink, GamePatches.with_game(game), ANY)

    mock_retcon_playthrough_filler.assert_called_once_with(ANY, ANY, ANY,
                                                           mock_random.return_value, status_update)

    mock_indices_for_unassigned_pickups.assert_called_once_with(mock_random.return_value, game,
                                                                filler_patches.pickup_assignment, ANY)
    filler_patches.assign_new_pickups.assert_called_once_with(mock_indices_for_unassigned_pickups.return_value)

    assert result == filler_patches.assign_new_pickups.return_value


@pytest.fixture(name="sky_temple_keys")
def sample_sky_temple_keys():
    return [
        PickupEntry("Test Sky Temple Key {}".format(i), tuple(), "sky_temple_key", 0)
        for i in range(1, 10)
    ]


def test_sky_temple_key_distribution_logic_vanilla_valid(dataclass_test_lib,
                                                         sky_temple_keys,
                                                         empty_patches):
    # Setup
    permalink = dataclass_test_lib.mock_dataclass(Permalink)
    permalink.layout_configuration.sky_temple_keys = LayoutSkyTempleKeyMode.VANILLA
    available_pickups = sky_temple_keys[:]

    # Run
    result = generator._sky_temple_key_distribution_logic(permalink, empty_patches, available_pickups)

    # Assert
    assert available_pickups == []
    assert result.pickup_assignment == dict(zip(generator._FLYING_ING_CACHES, sky_temple_keys))


def test_sky_temple_key_distribution_logic_vanilla_missing_pickup(dataclass_test_lib, empty_patches):
    # Setup
    permalink = dataclass_test_lib.mock_dataclass(Permalink)
    permalink.layout_configuration.sky_temple_keys = LayoutSkyTempleKeyMode.VANILLA
    available_pickups = []

    # Run
    with pytest.raises(GenerationFailure) as exp:
        generator._sky_temple_key_distribution_logic(permalink, empty_patches, available_pickups)

    assert exp.value == GenerationFailure(
        "Missing Sky Temple Keys in available_pickups to place in all requested boss places", permalink)


def test_sky_temple_key_distribution_logic_vanilla_used_location(dataclass_test_lib,
                                                                 sky_temple_keys,
                                                                 empty_patches):
    # Setup
    permalink = dataclass_test_lib.mock_dataclass(Permalink)
    permalink.layout_configuration.sky_temple_keys = LayoutSkyTempleKeyMode.VANILLA
    initial_pickup_assignment = {
        generator._FLYING_ING_CACHES[0]: PickupEntry("Other Item", tuple(), "other", 0)
    }
    patches = empty_patches.assign_new_pickups(initial_pickup_assignment.items())

    # Run
    with pytest.raises(GenerationFailure) as exp:
        generator._sky_temple_key_distribution_logic(permalink, patches, [sky_temple_keys[0]])

    assert exp.value == GenerationFailure(
        "Attempted to place '{}' in PickupIndex 45, but there's already 'Pickup Other Item' there".format(
            sky_temple_keys[0]
        ), permalink)


def test_sky_temple_key_distribution_logic_all_bosses_valid(dataclass_test_lib, sky_temple_keys, empty_patches):
    # Setup
    permalink = dataclass_test_lib.mock_dataclass(Permalink)
    permalink.layout_configuration.sky_temple_keys = LayoutSkyTempleKeyMode.ALL_BOSSES
    patches = empty_patches
    available_pickups = sky_temple_keys[:]

    # Run
    result = generator._sky_temple_key_distribution_logic(permalink, patches, available_pickups)

    # Assert
    assert available_pickups == []
    assert result.pickup_assignment == dict(zip(generator._GUARDIAN_INDICES + generator._SUB_GUARDIAN_INDICES,
                                                sky_temple_keys))


def test_sky_temple_key_distribution_logic_all_guardians_valid(dataclass_test_lib, sky_temple_keys, empty_patches):
    # Setup
    permalink = dataclass_test_lib.mock_dataclass(Permalink)
    permalink.layout_configuration.sky_temple_keys = LayoutSkyTempleKeyMode.ALL_GUARDIANS
    patches = empty_patches
    available_pickups = sky_temple_keys[:]

    # Run
    result = generator._sky_temple_key_distribution_logic(permalink, patches, available_pickups)

    # Assert
    assert available_pickups == sky_temple_keys[3:]
    assert result.pickup_assignment == dict(zip(generator._GUARDIAN_INDICES, sky_temple_keys))


def test_sky_temple_key_distribution_logic_fully_random_valid(dataclass_test_lib, sky_temple_keys, empty_patches):
    # Setup
    permalink = dataclass_test_lib.mock_dataclass(Permalink)
    permalink.layout_configuration.sky_temple_keys = LayoutSkyTempleKeyMode.FULLY_RANDOM
    patches = empty_patches
    available_pickups = sky_temple_keys[:]

    # Run
    result = generator._sky_temple_key_distribution_logic(permalink, patches, available_pickups)

    # Assert
    assert available_pickups == sky_temple_keys
    assert result.pickup_assignment == {}
