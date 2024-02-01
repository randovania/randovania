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
        return self.teleporter.area_location.region_name

    @property
    def area_name(self) -> str:
        return self.teleporter.area_location.area_name

    def connect_to(self, other: TeleporterHelper) -> None:
        self.destination = other.teleporter
        other.destination = self.teleporter
        self.connected_teleporter = other
        other.connected_teleporter = self

    @property
    def area_location(self) -> AreaIdentifier:
        return self.teleporter.area_location


def try_randomize_teleporters(
    rng: Random,
    teleporters: tuple[TeleporterHelper, ...],
) -> list[TeleporterHelper]:
    telepoter_database: list[TeleporterHelper] = list(teleporters)
    assert len(telepoter_database) % 2 == 0

    teleporter_list = copy.copy(telepoter_database)
    teleporters_by_region: dict[str, list[TeleporterHelper]] = defaultdict(list)
    for teleporter in teleporter_list:
        teleporters_by_region[teleporter.region_name].append(teleporter)

    while teleporter_list:
        source_teleporters: list[TeleporterHelper] = max(teleporters_by_region.values(), key=len)
        target_teleporters: list[TeleporterHelper] = [
            teleporter for teleporter in teleporter_list if teleporter not in source_teleporters
        ]
        source_teleporter = source_teleporters[0]
        target_teleporter = rng.choice(target_teleporters)

        source_teleporter.connect_to(target_teleporter)

        teleporters_by_region[source_teleporter.region_name].remove(source_teleporter)
        teleporters_by_region[target_teleporter.region_name].remove(target_teleporter)
        teleporter_list.remove(source_teleporter)
        teleporter_list.remove(target_teleporter)

    # TODO
    list3 = copy.copy(telepoter_database)
    cteleporter_list3 = [list3[0]]
    while list3:
        cteleporter_list1 = []
        for cteleporter1 in cteleporter_list3:
            index = 0
            while index < len(list3):
                cteleporter2 = list3[index]
                if (
                    cteleporter2.region_name == cteleporter1.region_name
                    or cteleporter2.area_name == cteleporter1.destination.area_name
                ):
                    cteleporter_list1.append(cteleporter2)
                    list3.remove(cteleporter2)
                else:
                    index += 1
        if cteleporter_list1:
            cteleporter_list3 = cteleporter_list1
        else:
            # Randomization failed
            return try_randomize_teleporters(rng, teleporters)

    return telepoter_database


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
        TeleporterHelper(region_list.identifier_for_node(node), node.default_connection)
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
