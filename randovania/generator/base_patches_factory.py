import copy
import dataclasses
from random import Random

from randovania.game_description import default_database
from randovania.game_description.area_location import AreaLocation
from randovania.game_description.assignment import GateAssignment
from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.hint import Hint, HintType, PrecisionPair, HintLocationPrecision, HintItemPrecision
from randovania.game_description.node import LogbookNode, LoreType
from randovania.game_description.resources.logbook_asset import LogbookAsset
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.world_list import WorldList
from randovania.generator import elevator_distributor
from randovania.layout.layout_configuration import LayoutElevators, LayoutConfiguration
from randovania.layout.translator_configuration import LayoutTranslatorRequirement


class MissingRng(Exception):
    pass


# M-Dhe -> E3B417BF -> Temple Grounds - Landing Site -> Defiled Shrine -> 11
# J-Fme -> 65206511 -> Temple Grounds - Industrial Site -> Accursed Lake -> 15
# D-Isl -> 28E8C41A -> Temple Grounds - Storage Cavern A -> Ing Reliquary -> 19
# J-Stl -> 150E8DB8 -> Agon Wastes - Central Mining Station -> Battleground -> 45
# B-Stl -> DE525E1D -> Agon Wastes - Main Reactor -> Dark Oasis -> 53
# S-Dly -> 58C62CB3 -> Torvus Bog - Torvus Lagoon -> Poisoned Bog -> 68
# G-Sch -> 939AFF16 -> Torvus Bog - Catacombs -> Dungeon -> 91
# C-Rch -> A9909E66 -> Sanctuary Fortress - Dynamo Works -> Hive Dynamo Works -> 106
# S-Jrs -> 62CC4DC3 -> Sanctuary Fortress - Sanctuary Entrance -> Hive Entrance -> 117

_KEYBEARERS_HINTS = {
    LogbookAsset(0xDE525E1D): PickupIndex(53),
    LogbookAsset(0xA9909E66): PickupIndex(106),
    LogbookAsset(0x28E8C41A): PickupIndex(19),
    LogbookAsset(0x939AFF16): PickupIndex(91),
    LogbookAsset(0x65206511): PickupIndex(15),
    LogbookAsset(0x150E8DB8): PickupIndex(45),
    LogbookAsset(0xE3B417BF): PickupIndex(11),
    LogbookAsset(0x58C62CB3): PickupIndex(68),
    LogbookAsset(0x62CC4DC3): PickupIndex(117),
}


def add_elevator_connections_to_patches(layout_configuration: LayoutConfiguration,
                                        rng: Random,
                                        patches: GamePatches) -> GamePatches:
    """
    :param layout_configuration:
    :param rng:
    :param patches:
    :return:
    """
    if layout_configuration.elevators != LayoutElevators.VANILLA:
        if rng is None:
            raise MissingRng("Elevator")

        world_list = default_database.default_prime2_game_description().world_list
        areas_to_not_change = {
            2278776548,  # Sky Temple Gateway
            2068511343,  # Sky Temple Energy Controller
            3136899603,  # Aerie Transport Station
            1564082177,  # Aerie
        }

        elevator_db = elevator_distributor.create_elevator_database(world_list, areas_to_not_change)

        if layout_configuration.elevators in {LayoutElevators.TWO_WAY_RANDOMIZED, LayoutElevators.TWO_WAY_UNCHECKED}:
            connections = elevator_distributor.two_way_elevator_connections(
                rng=rng,
                elevator_database=elevator_db,
                between_areas=layout_configuration.elevators == LayoutElevators.TWO_WAY_RANDOMIZED
            )
        else:
            connections = elevator_distributor.one_way_elevator_connections(
                rng=rng,
                elevator_database=elevator_db,
                world_list=world_list,
                elevator_target=layout_configuration.elevators == LayoutElevators.ONE_WAY_ELEVATOR
            )

        elevator_connection = copy.copy(patches.elevator_connection)
        elevator_connection.update(connections)
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
            if rng is None:
                raise MissingRng("Translator")
            requirement = rng.choice(choices)

        result[gate] = resource_database.get_by_type_and_index(ResourceType.ITEM, requirement.item_index)

    return result


def starting_location_for_configuration(configuration: LayoutConfiguration,
                                        game: GameDescription,
                                        rng: Random,
                                        ) -> AreaLocation:
    locations = list(configuration.starting_location.locations)
    if len(locations) == 0:
        raise ValueError("No available starting locations")
    elif len(locations) == 1:
        location = locations[0]
    else:
        if rng is None:
            raise MissingRng("Starting Location")
        location = rng.choice(locations)

    return location


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

    for node in world_list.all_nodes:
        if isinstance(node, LogbookNode) and node.lore_type == LoreType.LUMINOTH_WARRIOR:
            patches = patches.assign_hint(node.resource(),
                                          Hint(HintType.KEYBEARER,
                                               PrecisionPair(HintLocationPrecision.DETAILED,
                                                             HintItemPrecision.PRECISE_CATEGORY),
                                               PickupIndex(node.hint_index)))

    # TODO: this should be a flag in PickupNode
    indices_with_hint = [
        (PickupIndex(24), HintType.LIGHT_SUIT_LOCATION),  # Light Suit
        (PickupIndex(43), HintType.GUARDIAN),  # Dark Suit (Amorbis)
        (PickupIndex(79), HintType.GUARDIAN),  # Dark Visor (Chykka)
        (PickupIndex(115), HintType.GUARDIAN),  # Annihilator Beam (Quadraxis)
    ]
    all_logbook_assets = [node.resource()
                          for node in world_list.all_nodes
                          if isinstance(node, LogbookNode)
                          and node.resource() not in patches.hints
                          and node.lore_type.holds_generic_hint]

    rng.shuffle(indices_with_hint)
    rng.shuffle(all_logbook_assets)

    for index, hint_type in indices_with_hint:
        if not all_logbook_assets:
            break

        logbook_asset = all_logbook_assets.pop()
        patches = patches.assign_hint(logbook_asset, Hint(hint_type, PrecisionPair.detailed(), index))

    return patches


def create_base_patches(configuration: LayoutConfiguration,
                        rng: Random,
                        game: GameDescription,
                        ) -> GamePatches:
    """

    :param configuration:
    :param rng:
    :param game:
    :return:
    """

    # TODO: we shouldn't need the seed_number!

    patches = game.create_game_patches()
    patches = add_elevator_connections_to_patches(configuration, rng, patches)

    # Gates
    patches = patches.assign_gate_assignment(
        gate_assignment_for_configuration(configuration, game.resource_database, rng))

    # Starting Location
    patches = patches.assign_starting_location(
        starting_location_for_configuration(configuration, game, rng))

    # Hints
    if rng is not None:
        patches = add_default_hints_to_patches(rng, patches, game.world_list)

    return patches
