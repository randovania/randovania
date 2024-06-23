from __future__ import annotations

import copy
from collections import defaultdict
from typing import TYPE_CHECKING

from randovania.game_description.db.dock_node import DockNode
from randovania.generator.base_patches_factory import MissingRng
from randovania.layout.lib.teleporters import TeleporterConfiguration, TeleporterShuffleMode

if TYPE_CHECKING:
    from random import Random

    from randovania.game_description.db.area_identifier import AreaIdentifier
    from randovania.game_description.db.dock import DockType
    from randovania.game_description.db.node import Node
    from randovania.game_description.db.node_identifier import NodeIdentifier
    from randovania.game_description.db.region_list import RegionList
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.game_patches import TeleporterConnection


class TeleporterHelper:
    teleporter: NodeIdentifier
    destination: NodeIdentifier
    connected_teleporter: TeleporterHelper | None

    def __init__(self, teleporter: NodeIdentifier, destination: NodeIdentifier):
        self.teleporter = teleporter
        self.destination = destination
        self.connected_teleporter = None

    @property
    def region_name(self) -> str:
        return self.teleporter.area_identifier.region

    @property
    def area_name(self) -> str:
        return self.teleporter.area_identifier.area

    def connect_to(self, other: TeleporterHelper) -> None:
        self.destination = other.teleporter
        other.destination = self.teleporter
        self.connected_teleporter = other
        other.connected_teleporter = self

    @property
    def area_location(self) -> AreaIdentifier:
        return self.teleporter.area_identifier


def try_randomize_teleporters(
    rng: Random,
    teleporters: tuple[TeleporterHelper, ...],
) -> list[TeleporterHelper]:
    teleporter_database: list[TeleporterHelper] = list(teleporters)
    assert len(teleporter_database) % 2 == 0

    teleporter_list = copy.copy(teleporter_database)
    # sort all teleporters into a dict from region -> list of all teleporters in the region
    teleporters_by_region: dict[str, list[TeleporterHelper]] = defaultdict(list)
    for teleporter in teleporter_list:
        teleporters_by_region[teleporter.region_name].append(teleporter)

    while teleporter_list:
        # pick source_teleporters list with the most remaining teleporters
        source_teleporters: list[TeleporterHelper] = max(teleporters_by_region.values(), key=len)
        # create target_teleporters list => all (remaining) teleporters which
        # are not in the region from source_teleporters
        target_teleporters: list[TeleporterHelper] = [
            teleporter for teleporter in teleporter_list if teleporter not in source_teleporters
        ]
        # pick the first teleporter as source and a random target
        source_teleporter = source_teleporters[0]
        target_teleporter = rng.choice(target_teleporters)

        source_teleporter.connect_to(target_teleporter)

        # remove both connected teleporters from the list, eventually repeat until all teleporters are shuffled
        teleporters_by_region[source_teleporter.region_name].remove(source_teleporter)
        teleporters_by_region[target_teleporter.region_name].remove(target_teleporter)
        teleporter_list.remove(source_teleporter)
        teleporter_list.remove(target_teleporter)

    # check if all teleporters are reachable, which means this list must be empty at the end
    remaining_teleporters = copy.copy(teleporter_database)
    # start with a random reachable teleporter
    reachable_teleporters = [remaining_teleporters[0]]
    while remaining_teleporters:
        new_reachable_teleporters = []
        for reachable_teleporter in reachable_teleporters:
            index = 0
            # check all remaining teleporters
            while index < len(remaining_teleporters):
                teleporter_to_check = remaining_teleporters[index]
                # teleporter_to_check is considered reachable if it is in the same region as a reachable_teleporter
                # or if it is in the region+area of the reachable_teleporter's destination
                if (
                    teleporter_to_check.region_name == reachable_teleporter.region_name
                    or teleporter_to_check.area_location == reachable_teleporter.destination.area_identifier
                ):
                    new_reachable_teleporters.append(teleporter_to_check)
                    remaining_teleporters.remove(teleporter_to_check)
                else:
                    index += 1
        # next iteration should start with the new_reachable teleporters
        if new_reachable_teleporters:
            reachable_teleporters = new_reachable_teleporters
        # if new_reachable_teleporters is empty, it means that not all teleporters are reachable: shuffle again!
        else:
            # Randomization failed
            return try_randomize_teleporters(rng, teleporters)

    return teleporter_database


def two_way_teleporter_connections(
    rng: Random, teleporter_database: tuple[TeleporterHelper, ...], between_areas: bool
) -> TeleporterConnection:
    if len(teleporter_database) % 2 != 0:
        raise ValueError("Two-way teleporter shuffle, but odd number of teleporters to shuffle.")
    if between_areas:
        teleporter_database = tuple(try_randomize_teleporters(rng, teleporter_database))
    else:
        teleporters = list(teleporter_database)
        rng.shuffle(teleporters)
        while teleporters:
            teleporters.pop().connect_to(teleporters.pop())

    result: TeleporterConnection = {}
    for teleporter in teleporter_database:
        assert teleporter.connected_teleporter is not None
        result[teleporter.teleporter] = teleporter.connected_teleporter.teleporter

    return result


def one_way_teleporter_connections(
    rng: Random,
    teleporter_database: tuple[TeleporterHelper, ...],
    target_locations: list[NodeIdentifier],
    replacement: bool,
) -> TeleporterConnection:
    target_locations.sort()
    rng.shuffle(target_locations)

    def _create_target() -> NodeIdentifier:
        if replacement:
            return rng.choice(target_locations)
        else:
            return target_locations.pop()

    return {teleporter.teleporter: _create_target() for teleporter in teleporter_database}


def create_teleporter_database(
    region_list: RegionList, all_teleporters: list[NodeIdentifier], allowed_dock_types: list[DockType]
) -> tuple[TeleporterHelper, ...]:
    """
    Creates a tuple of Teleporter objects, exclude those that belongs to one of the areas provided.
    :param region_list:
    :param all_teleporters: Set of teleporters to use
    :return:
    """
    all_helpers = [
        TeleporterHelper(node.identifier, node.default_connection)
        for region, area, node in region_list.all_regions_areas_nodes
        if isinstance(node, DockNode) and node.dock_type in allowed_dock_types
    ]
    return tuple(helper for helper in all_helpers if helper.teleporter in all_teleporters)


def get_dock_connections_assignment_for_teleporter(
    teleporters: TeleporterConfiguration, game: GameDescription, teleporter_connection: TeleporterConnection
) -> list[tuple[DockNode, Node]]:
    region_list = game.region_list

    for teleporter, destination in teleporters.static_teleporters.items():
        teleporter_connection[teleporter] = destination

    assignment = [
        (region_list.typed_node_by_identifier(identifier, DockNode), region_list.node_by_identifier(target))
        for identifier, target in teleporter_connection.items()
    ]

    return assignment


def get_teleporter_connections(
    teleporters: TeleporterConfiguration, game: GameDescription, rng: Random
) -> TeleporterConnection:
    region_list = game.region_list
    teleporter_connection: TeleporterConnection = {}

    if not teleporters.is_vanilla:
        if rng is None:
            raise MissingRng("Teleporter")

        teleporter_dock_types = game.dock_weakness_database.all_teleporter_dock_types
        teleporter_db = create_teleporter_database(region_list, teleporters.editable_teleporters, teleporter_dock_types)

        # TODO: Error on unsupported modes
        if teleporters.mode in {TeleporterShuffleMode.TWO_WAY_RANDOMIZED, TeleporterShuffleMode.TWO_WAY_UNCHECKED}:
            connections = two_way_teleporter_connections(
                rng=rng,
                teleporter_database=teleporter_db,
                between_areas=teleporters.mode == TeleporterShuffleMode.TWO_WAY_RANDOMIZED,
            )
        else:
            connections = one_way_teleporter_connections(
                rng=rng,
                teleporter_database=teleporter_db,
                target_locations=teleporters.valid_targets,
                replacement=teleporters.mode != TeleporterShuffleMode.ONE_WAY_TELEPORTER,
            )

        teleporter_connection.update(connections)

    return teleporter_connection
