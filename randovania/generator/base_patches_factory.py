import copy
import dataclasses
from random import Random

from randovania.game_description import data_reader
from randovania.game_description.area_location import AreaLocation
from randovania.game_description.assignment import GateAssignment
from randovania.game_description.echoes_game_specific import EchoesGameSpecific
from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.hint import Hint, HintType, PrecisionPair, HintLocationPrecision, HintItemPrecision, \
    HintDarkTemple
from randovania.game_description.node import LogbookNode, LoreType
from randovania.game_description.resources.logbook_asset import LogbookAsset
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.world_list import WorldList
from randovania.games.game import RandovaniaGame
from randovania.generator import elevator_distributor
from randovania.interface_common.enum_lib import iterate_enum
from randovania.layout.echoes_configuration import EchoesConfiguration
from randovania.layout.elevators import LayoutElevators
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


def add_elevator_connections_to_patches(layout_configuration: EchoesConfiguration,
                                        rng: Random,
                                        patches: GamePatches) -> GamePatches:
    """
    :param layout_configuration:
    :param rng:
    :param patches:
    :return:
    """
    elevator_connection = copy.copy(patches.elevator_connection)

    if layout_configuration.elevators != LayoutElevators.VANILLA:
        if rng is None:
            raise MissingRng("Elevator")

        world_list = data_reader.decode_data(layout_configuration.game_data).world_list
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

        elevator_connection.update(connections)

    if layout_configuration.skip_final_bosses:
        elevator_connection[136970379] = AreaLocation(1006255871, 1393588666)

    return dataclasses.replace(patches, elevator_connection=elevator_connection)


def gate_assignment_for_configuration(configuration: EchoesConfiguration,
                                      resource_database: ResourceDatabase,
                                      rng: Random,
                                      ) -> GateAssignment:
    """
    :param configuration:
    :param resource_database:
    :param rng:
    :return:
    """

    all_choices = list(LayoutTranslatorRequirement)
    all_choices.remove(LayoutTranslatorRequirement.RANDOM)
    all_choices.remove(LayoutTranslatorRequirement.RANDOM_WITH_REMOVED)
    without_removed = copy.copy(all_choices)
    without_removed.remove(LayoutTranslatorRequirement.REMOVED)
    random_requirements = {LayoutTranslatorRequirement.RANDOM, LayoutTranslatorRequirement.RANDOM_WITH_REMOVED}

    result = {}
    for gate, requirement in configuration.translator_configuration.translator_requirement.items():
        if requirement in random_requirements:
            if rng is None:
                raise MissingRng("Translator")
            requirement = rng.choice(all_choices if requirement == LayoutTranslatorRequirement.RANDOM_WITH_REMOVED
                                     else without_removed)

        result[gate] = resource_database.get_by_type_and_index(ResourceType.ITEM, requirement.item_index)

    return result


def starting_location_for_configuration(configuration: EchoesConfiguration,
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


def add_echoes_default_hints_to_patches(rng: Random,
                                        patches: GamePatches,
                                        world_list: WorldList,
                                        num_joke: int,
                                        is_multiworld: bool,
                                        ) -> GamePatches:
    """
    Adds hints that are present on all games.
    :param rng:
    :param patches:
    :param world_list:
    :param num_joke
    :param is_multiworld
    :return:
    """

    for node in world_list.all_nodes:
        if isinstance(node, LogbookNode) and node.lore_type == LoreType.LUMINOTH_WARRIOR:
            patches = patches.assign_hint(node.resource(),
                                          Hint(HintType.LOCATION,
                                               PrecisionPair(HintLocationPrecision.KEYBEARER,
                                                             HintItemPrecision.BROAD_CATEGORY,
                                                             include_owner=True),
                                               PickupIndex(node.hint_index)))

    all_logbook_assets = [node.resource()
                          for node in world_list.all_nodes
                          if isinstance(node, LogbookNode)
                          and node.resource() not in patches.hints
                          and node.lore_type.holds_generic_hint]

    rng.shuffle(all_logbook_assets)

    # The 4 guaranteed hints
    indices_with_hint = [
        (PickupIndex(24), HintLocationPrecision.LIGHT_SUIT_LOCATION),  # Light Suit
        (PickupIndex(43), HintLocationPrecision.GUARDIAN),  # Dark Suit (Amorbis)
        (PickupIndex(79), HintLocationPrecision.GUARDIAN),  # Dark Visor (Chykka)
        (PickupIndex(115), HintLocationPrecision.GUARDIAN),  # Annihilator Beam (Quadraxis)
    ]
    rng.shuffle(indices_with_hint)
    for index, location_type in indices_with_hint:
        if not all_logbook_assets:
            break

        logbook_asset = all_logbook_assets.pop()
        patches = patches.assign_hint(logbook_asset, Hint(HintType.LOCATION,
                                                          PrecisionPair(location_type, HintItemPrecision.DETAILED,
                                                                        include_owner=False),
                                                          index))

    # Dark Temple hints
    temple_hints = list(iterate_enum(HintDarkTemple))
    while all_logbook_assets and temple_hints:
        logbook_asset = all_logbook_assets.pop()
        patches = patches.assign_hint(logbook_asset, Hint(HintType.RED_TEMPLE_KEY_SET, None,
                                                          dark_temple=temple_hints.pop(0)))

    # Jokes
    while num_joke > 0 and all_logbook_assets:
        logbook_asset = all_logbook_assets.pop()
        patches = patches.assign_hint(logbook_asset, Hint(HintType.JOKE, None))
        num_joke -= 1

    return patches


def create_game_specific(configuration: EchoesConfiguration, game: GameDescription) -> EchoesGameSpecific:
    if configuration.game == RandovaniaGame.PRIME2:
        return EchoesGameSpecific(
            energy_per_tank=configuration.energy_per_tank,
            safe_zone_heal_per_second=configuration.safe_zone.heal_per_second,
            beam_configurations=configuration.beam_configuration.create_game_specific(game.resource_database),
            dangerous_energy_tank=configuration.dangerous_energy_tank,
        )
    else:
        return game.game_specific


def create_base_patches(configuration: EchoesConfiguration,
                        rng: Random,
                        game: GameDescription,
                        is_multiworld: bool,
                        ) -> GamePatches:
    """
    """
    patches = dataclasses.replace(game.create_game_patches(),
                                  game_specific=create_game_specific(configuration, game))

    patches = add_elevator_connections_to_patches(configuration, rng, patches)

    # Gates
    if configuration.game == RandovaniaGame.PRIME2:
        patches = patches.assign_gate_assignment(
            gate_assignment_for_configuration(configuration, game.resource_database, rng))

    # Starting Location
    patches = patches.assign_starting_location(
        starting_location_for_configuration(configuration, game, rng))

    # Hints
    if rng is not None and configuration.game == RandovaniaGame.PRIME2:
        patches = add_echoes_default_hints_to_patches(rng, patches, game.world_list,
                                                      num_joke=2, is_multiworld=is_multiworld)

    return patches
