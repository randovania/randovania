import dataclasses
from random import Random

import pytest

from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.game_patches import GamePatches
from randovania.games.am2r.generator.pool_creator import artifact_pool
from randovania.games.am2r.layout import AM2RConfiguration
from randovania.games.game import RandovaniaGame
from randovania.generator.pickup_pool import pool_creator
from randovania.layout.exceptions import InvalidConfiguration


@pytest.fixture()
def configuration(preset_manager):
    configuration = preset_manager.default_preset_for_game(RandovaniaGame.AM2R).get_preset().configuration
    assert isinstance(configuration, AM2RConfiguration)
    return configuration


def test_am2r_pool_creator(am2r_game_description, preset_manager):
    # Setup
    preset = preset_manager.default_preset_for_game(am2r_game_description.game).get_preset()
    patches = GamePatches.create_from_game(am2r_game_description, 0, preset.configuration)

    # Run
    results = pool_creator.calculate_pool_results(
        preset.configuration,
        am2r_game_description,
        patches,
        Random(5000),
        True,
    )

    # Assert
    wl = am2r_game_description.region_list
    c = NodeIdentifier.create

    locations = [
        wl.identifier_for_node(wl.node_from_pickup_index(index))
        for index in results.assignment.keys()
    ]

    # Uncomment to easily see locations
    # assert locations == []

    assert locations == [
        c("Hydro Station", "Hydro Station Entrance", "Pickup (Alpha)"),
        c("The Tower", "Exterior Zeta Nest East", "Pickup (Zeta)"),
        c("Main Caves", "Mines Alpha Nest", "Pickup (Alpha)"),
        c("Distribution Center", "Alpha Squad Nest", "Pickup (Left Top Alpha)"),
        c("The Nest", "Depths Omega Nest South West", "Pickup (Omega)"),
        c("Industrial Complex", "Breeding Grounds Alpha Nest", "Pickup (Alpha)"),
        c("Distribution Center", "Alpha Squad Nest", "Pickup (Left Bottom Alpha)"),
        c("Industrial Complex", "Upper Factory Alpha Nest", "Pickup (Alpha)"),
        c("Distribution Center", "Alpha Squad Nest", "Pickup (Left Middle Alpha)"),
        c("Main Caves", "Surface Alpha Nest", "Pickup (Alpha)"),
    ]

    # 46 is total number of metroids
    assert len(results.to_place) == wl.num_pickup_nodes - (46 - len(locations)) - len(results.assignment)


@pytest.mark.parametrize("metroids, bosses, artifacts", [
    (False, False, 1), (False, True, 7), (True, False, 47), (True, True, 47)
])
def test_am2r_artifact_pool_should_throw_on_invalid_config(am2r_game_description, configuration,
                                                           metroids, bosses, artifacts):
    # Setup
    configuration = dataclasses.replace(
        configuration,
        artifacts=dataclasses.replace(configuration.artifacts,
                                      prefer_metroids=metroids, prefer_bosses=bosses, required_artifacts=artifacts))

    # Run
    with pytest.raises(InvalidConfiguration) as exception:
        artifact_pool(am2r_game_description, configuration, Random(5000))

    # Assert
    assert exception.type is InvalidConfiguration
    assert exception.value.args[0] == "More Metroid DNA than allowed!"


def test_am2r_artifact_pool_metroids(am2r_game_description, configuration):
    # Setup
    configuration = dataclasses.replace(configuration,
                                        artifacts=dataclasses.replace(configuration.artifacts,
                                                                      prefer_metroids=True, prefer_bosses=False,
                                                                      required_artifacts=46))

    # Run
    results = artifact_pool(am2r_game_description, configuration, Random(5000))

    # Assert
    assert results.to_place == []
    assert results.starting == []
    assert all(350 <= k.index <= 395 for k in results.assignment.keys())


def test_am2r_artifact_pool_bosses(am2r_game_description, configuration):
    # Setup
    configuration = dataclasses.replace(configuration,
                                        artifacts=dataclasses.replace(configuration.artifacts,
                                                                      prefer_metroids=False, prefer_bosses=True,
                                                                      required_artifacts=6))

    # Run
    results = artifact_pool(am2r_game_description, configuration, Random(5000))

    # Assert
    assert results.to_place == []
    assert len(results.starting) == 40
    assert all(k.index in _boss_indices for k in results.assignment.keys())


def test_am2r_artifact_pool_metroids_and_bosses(am2r_game_description, configuration):
    # Setup
    configuration = dataclasses.replace(configuration,
                                        artifacts=dataclasses.replace(configuration.artifacts,
                                                                      prefer_metroids=True, prefer_bosses=True,
                                                                      required_artifacts=46))

    # Run
    results = artifact_pool(am2r_game_description, configuration, Random(5000))

    # Assert
    assert results.to_place == []
    assert results.starting == []
    assert all((k.index in _boss_indices) or (350 <= k.index <= 395) for k in results.assignment.keys())


def test_am2r_artifact_pool_all_starting(am2r_game_description, configuration):
    # Setup
    configuration = dataclasses.replace(configuration,
                                        artifacts=dataclasses.replace(configuration.artifacts,
                                                                      prefer_metroids=False, prefer_bosses=False,
                                                                      required_artifacts=0))

    # Run
    results = artifact_pool(am2r_game_description, configuration, Random(5000))

    # Assert
    assert results.to_place == []
    assert len(results.starting) == 46
    assert results.assignment == {}


_boss_indices = [
    111,
    3,
    6,
    14,
    11,
    50
]
