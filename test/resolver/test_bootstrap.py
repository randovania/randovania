import dataclasses
from unittest.mock import MagicMock

import pytest

from randovania.game_description import default_database
from randovania.game_description.resources.resource_info import ResourceCollection
from randovania.game_description.resources.resource_type import ResourceType
from randovania.games.game import RandovaniaGame
from randovania.games.prime1.generator.bootstrap import PrimeBootstrap


@pytest.mark.parametrize("vanilla_elevators", [False, True])
def test_misc_resources_for_configuration(echoes_resource_database,
                                          vanilla_elevators: bool,
                                          ):
    # Setup
    configuration = MagicMock()
    configuration.game = RandovaniaGame.METROID_PRIME_ECHOES
    configuration.elevators.is_vanilla = vanilla_elevators
    gfmc_resource = echoes_resource_database.get_by_type_and_index(ResourceType.MISC, "VanillaGFMCGate")
    torvus_resource = echoes_resource_database.get_by_type_and_index(ResourceType.MISC, "VanillaTorvusTempleGate")
    great_resource = echoes_resource_database.get_by_type_and_index(ResourceType.MISC, "VanillaGreatTempleEmeraldGate")

    # Run
    result = dict(configuration.game.generator.bootstrap.misc_resources_for_configuration(
        configuration,
        echoes_resource_database,
    ))
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


def test_logic_bootstrap(preset_manager, game_enum, empty_patches):
    configuration = preset_manager.default_preset_for_game(game_enum).get_preset().configuration
    game = default_database.game_description_for(configuration.game)

    new_game, state = game_enum.generator.bootstrap.logic_bootstrap(
        configuration,
        game.get_mutable(),
        dataclasses.replace(empty_patches, configuration=configuration, starting_location=game.starting_location),
    )


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
    current_resources = ResourceCollection.from_dict({
        prime1_resource_database.get_item_by_name(suit): 1
        for suit in suits
    })
    bootstrap = RandovaniaGame.METROID_PRIME.generator.bootstrap
    assert isinstance(bootstrap, PrimeBootstrap)

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
    current_resources = ResourceCollection.from_dict({
        prime1_resource_database.get_item_by_name(suit): 1
        for suit in suits
    })
    bootstrap = RandovaniaGame.METROID_PRIME.generator.bootstrap
    assert isinstance(bootstrap, PrimeBootstrap)

    # Run
    result = bootstrap.prime1_absolute_damage_reduction(
        prime1_resource_database, current_resources)

    # Assert
    assert result == expected
