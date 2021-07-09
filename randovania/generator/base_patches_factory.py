import copy
import dataclasses
from random import Random

from randovania.game_description import default_database
from randovania.game_description.world.area_location import AreaLocation
from randovania.game_description.assignment import GateAssignment
from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.hint import Hint, HintType, PrecisionPair, HintLocationPrecision, HintItemPrecision, \
    HintDarkTemple
from randovania.game_description.world.node import LogbookNode, LoreType
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.world.world_list import WorldList
from randovania.games.game import RandovaniaGame
from randovania.generator import elevator_distributor
from randovania.lib.enum_lib import iterate_enum
from randovania.layout.prime2.echoes_configuration import EchoesConfiguration
from randovania.layout.lib.teleporters import TeleporterShuffleMode
from randovania.layout.prime2.translator_configuration import LayoutTranslatorRequirement


class MissingRng(Exception):
    pass


def add_elevator_connections_to_patches(configuration: EchoesConfiguration,
                                        rng: Random,
                                        patches: GamePatches) -> GamePatches:
    """
    :param configuration:
    :param rng:
    :param patches:
    :return:
    """
    elevator_connection = copy.copy(patches.elevator_connection)
    elevators = configuration.elevators

    if not elevators.is_vanilla:
        if rng is None:
            raise MissingRng("Elevator")

        world_list = default_database.game_description_for(configuration.game).world_list
        elevator_db = elevator_distributor.create_elevator_database(
            world_list, elevators.editable_teleporters)

        if elevators.mode in {TeleporterShuffleMode.TWO_WAY_RANDOMIZED, TeleporterShuffleMode.TWO_WAY_UNCHECKED}:
            connections = elevator_distributor.two_way_elevator_connections(
                rng=rng,
                elevator_database=elevator_db,
                between_areas=elevators.mode == TeleporterShuffleMode.TWO_WAY_RANDOMIZED
            )
        else:
            connections = elevator_distributor.one_way_elevator_connections(
                rng=rng,
                elevator_database=elevator_db,
                target_locations=elevators.valid_targets,
                replacement=elevators.mode == TeleporterShuffleMode.ONE_WAY_ELEVATOR_REPLACEMENT,
            )

        elevator_connection.update(connections)

    for teleporter, destination in elevators.static_teleporters.items():
        elevator_connection[teleporter] = destination

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


def create_base_patches(configuration: EchoesConfiguration,
                        rng: Random,
                        game: GameDescription,
                        is_multiworld: bool,
                        player_index: int,
                        ) -> GamePatches:
    """
    """
    patches = dataclasses.replace(game.create_game_patches(),
                                  player_index=player_index)

    patches = add_elevator_connections_to_patches(configuration, rng, patches)

    # Gates
    if configuration.game == RandovaniaGame.METROID_PRIME_ECHOES:
        patches = patches.assign_gate_assignment(
            gate_assignment_for_configuration(configuration, game.resource_database, rng))

    # Starting Location
    patches = patches.assign_starting_location(
        starting_location_for_configuration(configuration, game, rng))

    # Hints
    if rng is not None and configuration.game == RandovaniaGame.METROID_PRIME_ECHOES:
        patches = add_echoes_default_hints_to_patches(rng, patches, game.world_list,
                                                      num_joke=2, is_multiworld=is_multiworld)

    return patches
