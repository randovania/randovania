from __future__ import annotations

import dataclasses
from random import Random
from unittest.mock import MagicMock

import pytest

from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_type import ResourceType
from randovania.games.common.prime_family.layout.lib.prime_trilogy_teleporters import (
    PrimeTrilogyTeleporterConfiguration,
)
from randovania.games.prime2.generator.bootstrap import EchoesBootstrap
from randovania.games.prime2.generator.pickup_pool import sky_temple_keys
from randovania.games.prime2.layout.echoes_configuration import LayoutSkyTempleKeyMode
from randovania.generator.pickup_pool import pool_creator

_GUARDIAN_INDICES = [
    PickupIndex(43),  # Dark Suit
    PickupIndex(79),  # Dark Visor
    PickupIndex(115),  # Annihilator Beam
]
_SUB_GUARDIAN_INDICES = [
    PickupIndex(38),  # Morph Ball Bomb
    PickupIndex(37),  # Space Jump Boots
    PickupIndex(75),  # Boost Ball
    PickupIndex(86),  # Grapple Beam
    PickupIndex(102),  # Spider Ball
    PickupIndex(88),  # Main Power Bombs
]


@pytest.mark.parametrize("vanilla_teleporters", [False, True])
def test_misc_resources_for_configuration(
    echoes_resource_database,
    default_echoes_configuration,
    vanilla_teleporters: bool,
):
    # Setup
    teleporters = MagicMock(spec=PrimeTrilogyTeleporterConfiguration)
    configuration = dataclasses.replace(default_echoes_configuration, teleporters=teleporters)
    teleporters.is_vanilla = vanilla_teleporters
    gfmc_resource = echoes_resource_database.get_by_type_and_index(ResourceType.MISC, "VanillaGFMCGate")
    torvus_resource = echoes_resource_database.get_by_type_and_index(ResourceType.MISC, "VanillaTorvusTempleGate")
    great_resource = echoes_resource_database.get_by_type_and_index(ResourceType.MISC, "VanillaGreatTempleEmeraldGate")

    # Run
    result = dict(
        configuration.game.generator.bootstrap.misc_resources_for_configuration(
            configuration,
            echoes_resource_database,
        )
    )
    relevant_tricks = {trick: result[trick] for trick in [gfmc_resource, torvus_resource, great_resource]}

    # Assert
    assert relevant_tricks == {
        gfmc_resource: 0,
        torvus_resource: 0,
        great_resource: 0 if not vanilla_teleporters else 1,
    }


@pytest.mark.parametrize("stk_mode", LayoutSkyTempleKeyMode)
def test_assign_pool_results(echoes_game_description, default_echoes_configuration, stk_mode: LayoutSkyTempleKeyMode):
    patches = GamePatches.create_from_game(
        echoes_game_description, 0, dataclasses.replace(default_echoes_configuration, sky_temple_keys=stk_mode)
    )
    pool_results = pool_creator.calculate_pool_results(patches.configuration, patches.game)

    # Run
    result = EchoesBootstrap().assign_pool_results(
        Random(1000),
        patches,
        pool_results,
    )

    # Assert
    shuffled_stks = [
        pickup for pickup in pool_results.to_place if pickup.pickup_category == sky_temple_keys.SKY_TEMPLE_KEY_CATEGORY
    ]

    assert result.starting_equipment == pool_results.starting
    if stk_mode == LayoutSkyTempleKeyMode.ALL_BOSSES:
        assert len(shuffled_stks) == 0
        assert set(result.pickup_assignment.keys()) == set(_GUARDIAN_INDICES + _SUB_GUARDIAN_INDICES)

    elif stk_mode == LayoutSkyTempleKeyMode.ALL_GUARDIANS:
        assert len(shuffled_stks) == 0
        assert set(result.pickup_assignment.keys()) == set(_GUARDIAN_INDICES)

    else:
        assert len(shuffled_stks) == stk_mode.num_keys
