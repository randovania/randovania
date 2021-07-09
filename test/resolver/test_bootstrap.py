from unittest.mock import MagicMock

import pytest

from randovania.game_description.resources.resource_type import ResourceType
from randovania.games.game import RandovaniaGame
from randovania.resolver import bootstrap


@pytest.mark.parametrize("vanilla_elevators", [False, True])
def test_misc_resources_for_configuration(echoes_resource_database,
                                          vanilla_elevators: bool,
                                          ):
    # Setup
    configuration = MagicMock()
    configuration.game = RandovaniaGame.METROID_PRIME_ECHOES
    configuration.elevators.is_vanilla = vanilla_elevators
    gfmc_resource = echoes_resource_database.get_by_type_and_index(ResourceType.MISC, 16)
    torvus_resource = echoes_resource_database.get_by_type_and_index(ResourceType.MISC, 17)
    great_resource = echoes_resource_database.get_by_type_and_index(ResourceType.MISC, 18)

    # Run
    result = bootstrap.misc_resources_for_configuration(configuration, echoes_resource_database)
    relevant_tricks = {
        trick: result[trick]
        for trick in [gfmc_resource, torvus_resource, great_resource]
    }

    # Assert
    assert relevant_tricks == {
        gfmc_resource: 0,
        torvus_resource: 0,
        great_resource: 0 if not vanilla_elevators else 1,
    }


def test_logic_bootstrap(default_preset, echoes_game_description):
    new_game, state = bootstrap.logic_bootstrap(default_preset.configuration,
                                                echoes_game_description.make_mutable_copy(),
                                                echoes_game_description.create_game_patches())


@pytest.mark.parametrize(["expected", "suits"], [
    (1.0, []),
    (0.9, ["Varia Suit"]),
    (0.9, ["Gravity Suit"]),
    (0.9, ["Phazon Suit"]),
    (0.8, ["Varia Suit", "Phazon Suit"]),
    (0.8, ["Varia Suit", "Gravity Suit"]),
    (0.8, ["Gravity Suit", "Phazon Suit"]),
    (0.5, ["Varia Suit", "Gravity Suit", "Phazon Suit"]),
])
def test_prime1_progressive_damage_reduction(prime1_resource_database, expected, suits):
    # Setup
    current_resources = {
        prime1_resource_database.get_item_by_name(suit): 1
        for suit in suits
    }

    # Run
    result = bootstrap.prime1_progressive_damage_reduction(prime1_resource_database, current_resources)

    # Assert
    assert result == expected


@pytest.mark.parametrize(["expected", "suits"], [
    (1.0, []),
    (0.9, ["Varia Suit"]),
    (0.8, ["Gravity Suit"]),
    (0.5, ["Phazon Suit"]),
    (0.5, ["Varia Suit", "Phazon Suit"]),
    (0.8, ["Varia Suit", "Gravity Suit"]),
    (0.5, ["Gravity Suit", "Phazon Suit"]),
    (0.5, ["Varia Suit", "Gravity Suit", "Phazon Suit"]),
])
def test_prime1_absolute_damage_reduction(prime1_resource_database, expected, suits):
    # Setup
    current_resources = {
        prime1_resource_database.get_item_by_name(suit): 1
        for suit in suits
    }

    # Run
    result = bootstrap.prime1_absolute_damage_reduction(prime1_resource_database, current_resources)

    # Assert
    assert result == expected
