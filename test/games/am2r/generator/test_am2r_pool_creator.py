import dataclasses

from random import Random

import pytest
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.games.am2r.generator.pool_creator import artifact_pool
from randovania.generator.pickup_pool import pool_creator
from randovania.layout.exceptions import InvalidConfiguration


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
    assert locations == [
        c("The Nest", "Hideout Alpha Nest", "Pickup (Alpha)"),
        c("Main Caves", "Research Site", "Pickup (Left Alpha)"),
        c("Golden Temple", "Exterior Alpha Nest", "Pickup (Alpha)"),
        c("Industrial Complex", "Exterior Gamma Nest", "Pickup (Gamma)"),
        c("Golden Temple", "Breeding Grounds South East", "Pickup (Alpha)"),
        c("Distribution Center", "Alpha Squad Nest", "Pickup (Left Middle Alpha)"),
        c("Industrial Complex", "Breeding Grounds Gamma Nest East", "Pickup (Gamma)"),
        c("The Nest", "Hideout Omega Nest", "Pickup (Omega)"),
        c("Industrial Complex", "Lower Factory Gamma Nest", "Pickup (Gamma)"),
        c("The Nest", "Depths Omega Nest East", "Pickup (Omega)"),
        c("The Tower", "Exterior Zeta Nest West", "Pickup (Zeta)"),
        c("Main Caves", "Mines Alpha Nest", "Pickup (Alpha)"),
        c("The Tower", "Gamma Nest South East", "Pickup (Gamma)"),
        c("The Nest", "Depths Omega Nest South West", "Pickup (Omega)"),
        c("Hydro Station", "Exterior Alpha Nest", "Pickup (Alpha)"),
    ]

    assert len(results.to_place) == wl.num_pickup_nodes - 31 - len(results.assignment)


@pytest.mark.parametrize("metroids, bosses, artifacts", [(False, False, 1), (False, True, 7), (True, False, 47), (True, True, 47)])
def test_am2r_artifact_pool_should_throw_on_invalid_config(am2r_game_description, preset_manager, metroids, bosses, artifacts):
    # Setup
    configuration = preset_manager.default_preset_for_game(am2r_game_description.game).get_preset().configuration

    configuration = dataclasses.replace(configuration,
                                        artifacts=dataclasses.replace(configuration.artifacts,
                                                                      prefer_metroids=metroids, prefer_bosses=bosses, required_artifacts=artifacts))

    # Run
    with pytest.raises(InvalidConfiguration) as exception:
        artifact_pool(am2r_game_description, configuration, Random(5000))

    # Assert
    assert exception.type is InvalidConfiguration
    assert exception.value.args[0] == "More Metroid DNA than allowed!"


def test_am2r_artifact_pool_metroids(am2r_game_description, preset_manager):
    # Setup
    configuration = preset_manager.default_preset_for_game(am2r_game_description.game).get_preset().configuration

    configuration = dataclasses.replace(configuration,
                                        artifacts=dataclasses.replace(configuration.artifacts,
                                                                      prefer_metroids=True, prefer_bosses=False, required_artifacts=46))

    # Run
    results = artifact_pool(am2r_game_description, configuration, Random(5000))

    # Assert
    assert results.to_place == []
    assert results.starting == []
    assert all(350 <= k.index <= 395 for k in results.assignment.keys())


def test_am2r_artifact_pool_bosses(am2r_game_description, preset_manager):
    # Setup
    configuration = preset_manager.default_preset_for_game(am2r_game_description.game).get_preset().configuration

    configuration = dataclasses.replace(configuration,
                                        artifacts=dataclasses.replace(configuration.artifacts,
                                                                      prefer_metroids=False, prefer_bosses=True, required_artifacts=6))

    # Run
    results = artifact_pool(am2r_game_description, configuration, Random(5000))

    # Assert
    assert results.to_place == []
    assert len(results.starting) == 40
    assert all(k.index in _boss_indices for k in results.assignment.keys())


def test_am2r_artifact_pool_metroids_and_bosses(am2r_game_description, preset_manager):
    # Setup
    configuration = preset_manager.default_preset_for_game(am2r_game_description.game).get_preset().configuration

    configuration = dataclasses.replace(configuration,
                                        artifacts=dataclasses.replace(configuration.artifacts,
                                                                      prefer_metroids=True, prefer_bosses=True, required_artifacts=46))

    # Run
    results = artifact_pool(am2r_game_description, configuration, Random(5000))

    # Assert
    assert results.to_place == []
    assert results.starting == []
    assert all((k.index in _boss_indices) or (350 <= k.index <= 395) for k in results.assignment.keys())


def test_am2r_artifact_pool_all_starting(am2r_game_description, preset_manager):
    # Setup
    configuration = preset_manager.default_preset_for_game(am2r_game_description.game).get_preset().configuration

    configuration = dataclasses.replace(configuration,
                                        artifacts=dataclasses.replace(configuration.artifacts,
                                                                      prefer_metroids=False, prefer_bosses=False, required_artifacts=0))

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