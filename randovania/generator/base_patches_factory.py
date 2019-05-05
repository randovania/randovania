import copy
import dataclasses
from random import Random

from randovania.game_description.area_location import AreaLocation
from randovania.game_description.assignment import GateAssignment
from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.hint import Hint, HintType, PrecisionPair
from randovania.game_description.node import LogbookNode
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.world_list import WorldList
from randovania.generator import elevator_distributor
from randovania.layout.layout_configuration import LayoutElevators, LayoutConfiguration
from randovania.layout.permalink import Permalink
from randovania.layout.starting_location import StartingLocationConfiguration
from randovania.layout.translator_configuration import LayoutTranslatorRequirement


def add_elevator_connections_to_patches(permalink: Permalink,
                                        patches: GamePatches) -> GamePatches:
    """

    :param permalink:
    :param patches:
    :return:
    """
    if permalink.layout_configuration.elevators == LayoutElevators.RANDOMIZED:
        elevator_connection = copy.copy(patches.elevator_connection)
        elevator_connection.update(elevator_distributor.elevator_connections_for_seed_number(permalink.seed_number))
        return dataclasses.replace(patches, elevator_connection=elevator_connection)
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


def add_default_hints_to_patches(rng: Random,
                                 patches: GamePatches,
                                 world_list: WorldList,
                                 ) -> GamePatches:
    """
    Adds hints for the locations
    :param rng:
    :param patches:
    :param world_list:
    :return:
    """
    # TODO: this should be a flag in PickupNode
    indices_with_hint = [
        PickupIndex(24),  # Light Suit
        PickupIndex(43),  # Dark Suit
        PickupIndex(79),  # Dark Visor
        PickupIndex(115),  # Annihilator Beam
    ]
    all_logbook_assets = [node.resource()
                          for node in world_list.all_nodes
                          if isinstance(node, LogbookNode) and node.resource() not in patches.hints]

    rng.shuffle(indices_with_hint)
    rng.shuffle(all_logbook_assets)

    for index in indices_with_hint:
        if not all_logbook_assets:
            break

        logbook_asset = all_logbook_assets.pop()
        patches = patches.assign_hint(logbook_asset, Hint(HintType.LOCATION, PrecisionPair.detailed(), index))

    return patches


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

    # Hints
    patches = add_default_hints_to_patches(rng, patches, game.world_list)

    return patches
