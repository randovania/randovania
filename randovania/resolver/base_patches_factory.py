import dataclasses
from random import Random

from randovania.game_description.area_location import AreaLocation
from randovania.game_description.assignment import GateAssignment
from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_type import ResourceType
from randovania.layout.layout_configuration import LayoutElevators, LayoutConfiguration
from randovania.layout.permalink import Permalink
from randovania.layout.starting_location import StartingLocationConfiguration
from randovania.layout.translator_configuration import LayoutTranslatorRequirement
from randovania.resolver import elevator_distributor


def add_elevator_connections_to_patches(permalink: Permalink,
                                        patches: GamePatches) -> GamePatches:
    assert patches.elevator_connection == {}
    if permalink.layout_configuration.elevators == LayoutElevators.RANDOMIZED:
        return dataclasses.replace(
            patches,
            elevator_connection=elevator_distributor.elevator_connections_for_seed_number(permalink.seed_number))
    else:
        return patches


def gate_assignment_for_configuration(configuration: LayoutConfiguration,
                                      resource_database: ResourceDatabase,
                                      rng: Random,
                                      ) -> GateAssignment:
    """
    :param configuration:
    :param resource_database:
    :param rng:
    :return:
    """

    choices = list(LayoutTranslatorRequirement)
    choices.remove(LayoutTranslatorRequirement.RANDOM)

    result = {}
    for gate, requirement in configuration.translator_configuration.translator_requirement.items():
        if requirement == LayoutTranslatorRequirement.RANDOM:
            requirement = rng.choice(choices)

        result[gate] = resource_database.get_by_type_and_index(ResourceType.ITEM, requirement.item_index)

    return result


def starting_location_for_configuration(configuration: LayoutConfiguration,
                                        game: GameDescription,
                                        rng: Random,
                                        ) -> AreaLocation:
    starting_location = configuration.starting_location

    if starting_location.configuration == StartingLocationConfiguration.SHIP:
        return game.starting_location

    elif starting_location.configuration == StartingLocationConfiguration.CUSTOM:
        return starting_location.custom_location

    elif starting_location.configuration == StartingLocationConfiguration.RANDOM_SAVE_STATION:
        save_stations = [node for node in game.world_list.all_nodes if node.name == "Save Station"]
        save_station = rng.choice(save_stations)
        return game.world_list.node_to_area_location(save_station)

    else:
        raise ValueError("Invalid configuration for StartLocation {}".format(starting_location))


def create_base_patches(rng: Random,
                        game: GameDescription,
                        permalink: Permalink,
                        ) -> GamePatches:
    """

    :param rng:
    :param game:
    :param permalink:
    :return:
    """

    patches = GamePatches.with_game(game)
    patches = add_elevator_connections_to_patches(permalink, patches)

    # Gates
    patches = patches.assign_gate_assignment(
        gate_assignment_for_configuration(permalink.layout_configuration, game.resource_database, rng))

    # Starting Location
    patches = patches.assign_starting_location(
        starting_location_for_configuration(permalink.layout_configuration, game, rng))

    return patches
