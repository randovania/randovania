from functools import partial
from pprint import pprint
from typing import List, Callable, TypeVar, BinaryIO, Tuple

from randovania import log_parser
from randovania.binary_source import BinarySource
from randovania.game_description import DamageReduction, SimpleResourceInfo, DamageResourceInfo, \
    IndividualRequirement, \
    DockWeakness, RequirementSet, World, Area, Node, GenericNode, DockNode, PickupNode, TeleporterNode, EventNode, \
    GameDescription, ResourceType, ResourceDatabase, DockType, DockWeaknessDatabase
from randovania.log_parser import PickupEntry

X = TypeVar('X')


def read_array(source: BinarySource, item_reader: Callable[[BinarySource], X]) -> List[X]:
    count = source.read_byte()
    return [
        item_reader(source)
        for _ in range(count)
    ]


def read_damage_reduction(source: BinarySource) -> DamageReduction:
    index = source.read_byte()
    multiplier = source.read_float()
    return DamageReduction(index, multiplier)


def read_damage_reductions(source: BinarySource) -> Tuple[DamageReduction, ...]:
    return tuple(read_array(source, read_damage_reduction))


def read_resource_info(source: BinarySource) -> SimpleResourceInfo:
    index = source.read_byte()
    long_name = source.read_string()
    short_name = source.read_string()
    return SimpleResourceInfo(index, long_name, short_name)


def read_resource_info_array(source: BinarySource) -> List[SimpleResourceInfo]:
    return read_array(source, read_resource_info)


def read_damage_resource_info(source: BinarySource) -> DamageResourceInfo:
    index = source.read_byte()
    long_name = source.read_string()
    short_name = source.read_string()
    return DamageResourceInfo(index, long_name, short_name, read_damage_reductions(source))


def read_damage_resource_info_array(source: BinarySource) -> List[DamageResourceInfo]:
    return read_array(source, read_damage_resource_info)


# Requirement

def read_individual_requirement(source: BinarySource, resource_database: ResourceDatabase) -> IndividualRequirement:
    requirement_type = ResourceType(source.read_byte())
    requirement_index = source.read_byte()
    amount = source.read_short()
    negate = source.read_bool()
    return IndividualRequirement.with_data(resource_database, requirement_type, requirement_index, amount,
                                           negate)


def read_requirement_list(source: BinarySource,
                          resource_database: ResourceDatabase) -> Tuple[IndividualRequirement, ...]:
    return tuple(read_array(source, partial(read_individual_requirement, resource_database=resource_database)))


def read_requirement_set(source: BinarySource, resource_database: ResourceDatabase) -> RequirementSet:
    return RequirementSet(
        tuple(read_array(source, partial(read_requirement_list, resource_database=resource_database))))


# Dock Weakness

def read_dock_weakness_database(source: BinarySource, resource_database: ResourceDatabase) -> DockWeaknessDatabase:
    def read_dock_weakness(source: BinarySource) -> DockWeakness:
        index = source.read_byte()
        name = source.read_string()
        is_blast_door = source.read_bool()
        requirement_set = read_requirement_set(source, resource_database)
        return DockWeakness(index, name, is_blast_door, requirement_set)

    door_types = read_array(source, read_dock_weakness)
    portal_types = read_array(source, read_dock_weakness)
    return DockWeaknessDatabase(
        door=door_types,
        morph_ball=[DockWeakness(0, "Morph Ball Door", False, RequirementSet.empty())],
        other=[DockWeakness(0, "Other Door", False, RequirementSet.empty())],
        portal=portal_types
    )


class WorldReader:
    resource_database: ResourceDatabase
    dock_weakness_database: DockWeaknessDatabase
    pickup_entries: List[PickupEntry]
    generic_index: int = 0

    def __init__(self, resource_database: ResourceDatabase, dock_weakness_database: DockWeaknessDatabase,
                 pickup_entries: List[PickupEntry]):
        self.resource_database = resource_database
        self.dock_weakness_database = dock_weakness_database
        self.pickup_entries = pickup_entries

    def read_node(self, source: BinarySource) -> Node:
        name = source.read_string()
        heal = source.read_bool()
        node_type = source.read_byte()

        if node_type == 0:
            self.generic_index += 1
            return GenericNode(name, heal, self.generic_index)

        elif node_type == 1:
            dock_index = source.read_byte()
            connected_area_asset_id = source.read_uint()
            connected_dock_index = source.read_byte()
            dock_type = DockType(source.read_byte())
            dock_weakness_index = source.read_byte()
            source.skip(3)
            return DockNode(name, heal, dock_index, connected_area_asset_id, connected_dock_index,
                            self.dock_weakness_database.get_by_type_and_index(dock_type, dock_weakness_index))

        elif node_type == 2:
            pickup_index = source.read_byte()
            return PickupNode(name, heal, self.pickup_entries[pickup_index])

        elif node_type == 3:
            destination_world_asset_id = source.read_uint()
            destination_area_asset_id = source.read_uint()
            teleporter_instance_id = source.read_uint()
            return TeleporterNode(name, heal, destination_world_asset_id, destination_area_asset_id,
                                  teleporter_instance_id)

        elif node_type == 4:
            event_index = source.read_byte()
            return EventNode(name, heal,
                             self.resource_database.get_by_type_and_index(ResourceType.EVENT, event_index))

        else:
            raise Exception("Unknown node type: {}".format(node_type))

    def read_area(self, source: BinarySource) -> Area:
        name = source.read_string()
        asset_id = source.read_uint()
        node_count = source.read_byte()
        default_node_index = source.read_byte()

        # TODO: hardcoded data fix
        # Aerie Transport Station has default_node_index not set
        if asset_id == 3136899603:
            default_node_index = 2

        nodes = [
            self.read_node(source)
            for _ in range(node_count)
        ]
        for node in nodes:  # type: PickupNode
            if isinstance(node, PickupNode):
                if node.pickup.room != name:
                    raise ValueError(
                        "Pickup at {}/{} has area name mismatch ({})".format(name, node.name, node.pickup.room))

        connections = {
            origin: {
                target: read_requirement_set(source, self.resource_database)
                for target in nodes
                if origin != target
            }
            for origin in nodes
        }
        # TODO: hardcoded data fix
        # Hive Temple Access has incorrect requirements for unlocking Hive Temple gate
        if asset_id == 3968294891:
            connections[nodes[1]][nodes[2]] = RequirementSet(tuple([
                tuple([
                    IndividualRequirement.with_data(self.resource_database, ResourceType.ITEM, 38 + i, 1, False)
                    for i in range(3)
                ])
            ]))
        return Area(name, asset_id, default_node_index, nodes, connections)

    def read_area_list(self, source: BinarySource) -> List[Area]:
        return read_array(source, self.read_area)

    def read_world(self, source: BinarySource) -> World:
        name = source.read_string()
        asset_id = source.read_uint()
        areas = self.read_area_list(source)
        return World(name, asset_id, areas)

    def read_world_list(self, source: BinarySource) -> List[World]:
        return read_array(source, self.read_world)


def parse_file(x: BinaryIO, pickup_entries: List[PickupEntry]) -> GameDescription:
    if x.read(4) != b"Req.":
        raise Exception("Invalid file format.")

    source = BinarySource(x)

    format_version = source.read_uint()
    if format_version != 6:
        raise Exception("Unsupported format version: {}, expected 5".format(format_version))

    game = source.read_byte()
    game_name = source.read_string()

    items = read_resource_info_array(source)
    events = read_resource_info_array(source)
    tricks = read_resource_info_array(source)
    damage = read_damage_resource_info_array(source)
    versions = read_resource_info_array(source)
    misc = read_resource_info_array(source)
    source.skip(1)  # Undocumented null byte
    difficulty = read_resource_info_array(source)

    resource_database = ResourceDatabase(item=items, event=events, trick=tricks, damage=damage, version=versions,
                                         misc=misc, difficulty=difficulty)
    dock_weakness_database = read_dock_weakness_database(source, resource_database)

    world_reader = WorldReader(resource_database, dock_weakness_database, pickup_entries)
    worlds = world_reader.read_world_list(source)

    final_boss = [event for event in events if event.long_name == "Emperor Ing"][0]
    victory_condition = RequirementSet(tuple([
        tuple([IndividualRequirement(final_boss, 1, False)])
    ]))

    nodes_to_area = {}
    nodes_to_world = {}
    for world in worlds:
        for area in world.areas:
            for node in area.nodes:
                if node in nodes_to_area:
                    raise ValueError("Trying to map {} to {}, but already mapped to {}".format(
                        node, area, nodes_to_area[node]
                    ))
                nodes_to_area[node] = area
                nodes_to_world[node] = world

    return GameDescription(
        game=game,
        game_name=game_name,
        resource_database=resource_database,
        dock_weakness_database=dock_weakness_database,
        worlds=worlds,
        nodes_to_area=nodes_to_area,
        nodes_to_world=nodes_to_world,
        victory_condition=victory_condition
    )


def read(path, pickup_entries: List[PickupEntry]) -> GameDescription:
    with open(path, "rb") as x:  # type: BinaryIO
        return parse_file(x, pickup_entries)
