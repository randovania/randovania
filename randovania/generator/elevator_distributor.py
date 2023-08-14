from __future__ import annotations

import copy
from collections import defaultdict
from typing import TYPE_CHECKING

from randovania.game_description.db.area_identifier import AreaIdentifier
from randovania.game_description.db.dock_node import DockNode
from randovania.generator.base_patches_factory import MissingRng
from randovania.layout.lib.teleporters import TeleporterShuffleMode

if TYPE_CHECKING:
    from random import Random

    from randovania.game_description.db.dock import DockType
    from randovania.game_description.db.node_identifier import NodeIdentifier
    from randovania.game_description.db.region_list import RegionList
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.game_patches import ElevatorConnection
    from randovania.games.dread.layout.dread_configuration import DreadConfiguration
    from randovania.games.prime1.layout.prime_configuration import PrimeConfiguration
    from randovania.games.prime2.layout.echoes_configuration import EchoesConfiguration

class ElevatorHelper:
    teleporter: NodeIdentifier
    destination: NodeIdentifier
    connected_elevator: ElevatorHelper | None

    def __init__(self, teleporter: NodeIdentifier, destination: NodeIdentifier):
        self.teleporter = teleporter
        self.destination = destination
        self.connected_elevator = None

    @property
    def region_name(self):
        return self.teleporter.area_location.region_name

    @property
    def area_name(self):
        return self.teleporter.area_location.area_name

    def connect_to(self, other: ElevatorHelper):
        self.destination = other.teleporter
        other.destination = self.teleporter
        self.connected_elevator = other
        other.connected_elevator = self

    @property
    def area_location(self):
        return self.teleporter.area_location


def try_randomize_elevators(rng: Random,
                            echoes_elevators: tuple[ElevatorHelper, ...],
                            ) -> list[ElevatorHelper]:
    elevator_database: list[ElevatorHelper] = list(echoes_elevators)
    assert len(elevator_database) % 2 == 0

    elevator_list = copy.copy(elevator_database)
    elevators_by_region: dict[str, list[ElevatorHelper]] = defaultdict(list)
    for elevator in elevator_list:
        elevators_by_region[elevator.region_name].append(elevator)

    while elevator_list:
        source_elevators: list[ElevatorHelper] = max(elevators_by_region.values(), key=len)
        target_elevators: list[ElevatorHelper] = [
            elevator
            for elevator in elevator_list
            if elevator not in source_elevators
        ]
        source_elevator = source_elevators[0]
        target_elevator = rng.choice(target_elevators)

        source_elevator.connect_to(target_elevator)

        elevators_by_region[source_elevator.region_name].remove(source_elevator)
        elevators_by_region[target_elevator.region_name].remove(target_elevator)
        elevator_list.remove(source_elevator)
        elevator_list.remove(target_elevator)

    # TODO
    list3 = copy.copy(elevator_database)
    celevator_list3 = [list3[0]]
    while list3:
        celevator_list1 = []
        for celevator1 in celevator_list3:
            index = 0
            while index < len(list3):
                celevator2 = list3[index]
                if (celevator2.region_name == celevator1.region_name
                        or celevator2.area_name == celevator1.destination.area_name):
                    celevator_list1.append(celevator2)
                    list3.remove(celevator2)
                else:
                    index += 1
        if celevator_list1:
            celevator_list3 = celevator_list1
        else:
            # Randomization failed
            return try_randomize_elevators(rng, echoes_elevators)

    return elevator_database


def two_way_elevator_connections(rng: Random,
                                 elevator_database: tuple[ElevatorHelper, ...],
                                 between_areas: bool
                                 ) -> ElevatorConnection:
    if len(elevator_database) % 2 != 0:
        raise ValueError("Two-way elevator shuffle, but odd number of elevators to shuffle.")
    if between_areas:
        elevator_database = try_randomize_elevators(rng, elevator_database)
    else:
        elevators = list(elevator_database)
        rng.shuffle(elevators)
        while elevators:
            elevators.pop().connect_to(elevators.pop())

    return {
        elevator.teleporter: elevator.connected_elevator.teleporter
        for elevator in elevator_database
    }


def one_way_elevator_connections(rng: Random,
                                 elevator_database: tuple[ElevatorHelper, ...],
                                 target_locations: list[NodeIdentifier],
                                 replacement: bool,
                                 ) -> ElevatorConnection:
    target_locations.sort()
    rng.shuffle(target_locations)

    def _create_target():
        if replacement:
            return rng.choice(target_locations)
        else:
            return target_locations.pop()

    return {
        elevator.teleporter: _create_target()
        for elevator in elevator_database
    }


def create_elevator_database(region_list: RegionList,
                             all_teleporters: list[NodeIdentifier],
                             allowed_dock_types: list[DockType]
                             ) -> tuple[ElevatorHelper, ...]:
    """
    Creates a tuple of Elevator objects, exclude those that belongs to one of the areas provided.
    :param region_list:
    :param all_teleporters: Set of teleporters to use
    :return:
    """
    all_helpers = [
        ElevatorHelper(region_list.identifier_for_node(node), node.default_connection.area_identifier)

        for region, area, node in region_list.all_regions_areas_nodes
        if isinstance(node, DockNode) and node.dock_type in allowed_dock_types
    ]
    return tuple(
        helper
        for helper in all_helpers
        if helper.teleporter in all_teleporters
    )

# TODO: Move to different file?

def get_dock_connections_for_elevators(configuration: PrimeConfiguration | EchoesConfiguration | DreadConfiguration,
                                       game: GameDescription, rng: Random
                                        ):
        elevators = configuration.elevators

        region_list = game.region_list
        elevator_connection: ElevatorConnection = {}

        if not elevators.is_vanilla:
            if rng is None:
                raise MissingRng("Elevator")

            elevator_dock_types = game.dock_weakness_database.all_teleporter_dock_types
            elevator_db = create_elevator_database(region_list, elevators.editable_teleporters,
                                                                        elevator_dock_types)
            if elevators.mode == TeleporterShuffleMode.ECHOES_SHUFFLED:
                connections = elevator_echoes_shuffled(game, rng)

            elif elevators.mode in {TeleporterShuffleMode.TWO_WAY_RANDOMIZED, TeleporterShuffleMode.TWO_WAY_UNCHECKED}:
                connections = two_way_elevator_connections(
                    rng=rng,
                    elevator_database=elevator_db,
                    between_areas=elevators.mode == TeleporterShuffleMode.TWO_WAY_RANDOMIZED
                )
            else:
                connections = one_way_elevator_connections(
                    rng=rng,
                    elevator_database=elevator_db,
                    target_locations=elevators.valid_targets,
                    replacement=elevators.mode != TeleporterShuffleMode.ONE_WAY_ELEVATOR,
                )

            elevator_connection.update(connections)

        for teleporter, destination in elevators.static_teleporters.items():
            elevator_connection[teleporter] = destination

        assignment = [
            (region_list.typed_node_by_identifier(identifier, DockNode), region_list.node_by_identifier(target))
            for identifier, target in elevator_connection.items()
        ]

        return assignment

def elevator_echoes_shuffled(game_description: GameDescription, rng: Random) -> ElevatorConnection:
        from randovania.games.prime2.generator.base_patches_factory import WORLDS
        worlds = list(WORLDS)
        rng.shuffle(worlds)

        result = {}

        def area_to_node(identifier: AreaIdentifier):
            area = game_description.region_list.area_by_area_location(identifier)
            for node in area.actual_nodes:
                if node.valid_starting_location:
                    return node.identifier
            raise KeyError(f"{identifier} has no valid starting location")

        def link_to(source: AreaIdentifier, target: AreaIdentifier):
            result[area_to_node(source)] = area_to_node(target)
            result[area_to_node(target)] = area_to_node(source)

        def tg_link_to(source: str, target: AreaIdentifier):
            link_to(AreaIdentifier("Temple Grounds", source), target)

        # TG -> GT
        tg_link_to("Temple Transport A", worlds[0].front)
        tg_link_to("Temple Transport B", worlds[0].left)
        tg_link_to("Temple Transport C", worlds[0].right)

        tg_link_to("Transport to Agon Wastes", worlds[1].front)
        tg_link_to("Transport to Torvus Bog", worlds[2].front)
        tg_link_to("Transport to Sanctuary Fortress", worlds[3].front)

        # inter areas
        link_to(worlds[1].right, worlds[2].left)
        link_to(worlds[2].right, worlds[3].left)
        link_to(worlds[3].right, worlds[1].left)

        return result
