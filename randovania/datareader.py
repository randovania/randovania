import pprint
import struct
from functools import partial
from typing import List

from randovania.game_description import DamageReduction, SimpleResourceInfo, DamageResourceInfo, \
    IndividualRequirement, \
    DockWeakness, RequirementSet, World, Area, Node, GenericNode, DockNode, PickupNode, TeleporterNode, EventNode, \
    RandomizerFileData, ResourceType, ResourceDatabase, DockType, DockWeaknessDatabase


def read_byte(file) -> int:
    return struct.unpack("!B", file.read(1))[0]


def read_short(file) -> int:
    return struct.unpack("!H", file.read(2))[0]


def read_uint(file) -> int:
    return struct.unpack("!I", file.read(4))[0]


def read_float(file) -> float:
    return struct.unpack("!f", file.read(4))[0]


def read_bool(file) -> bool:
    return struct.unpack("!?", file.read(1))[0]


def read_string(file) -> str:
    chars = []
    while True:
        c = file.read(1)
        if c[0] == 0:
            return b"".join(chars).decode("UTF-8")
        chars.append(c)


def read_array(x, item_reader):
    count = read_byte(x)
    return [
        item_reader(x)
        for _ in range(count)
    ]


def read_damage_reduction(x) -> DamageReduction:
    index = read_byte(x)
    multiplier = read_float(x)
    return DamageReduction(index, multiplier)


def read_damage_reductions(x) -> List[DamageReduction]:
    return read_array(x, read_damage_reduction)


def read_resource_info(x) -> SimpleResourceInfo:
    index = read_byte(x)
    long_name = read_string(x)
    short_name = read_string(x)
    return SimpleResourceInfo(index, long_name, short_name)


def read_resource_info_array(x) -> List[SimpleResourceInfo]:
    return read_array(x, read_resource_info)


def read_damage_resource_info(x) -> DamageResourceInfo:
    index = read_byte(x)
    long_name = read_string(x)
    short_name = read_string(x)
    return DamageResourceInfo(index, long_name, short_name, read_damage_reductions(x))


def read_damage_resource_info_array(x) -> List[DamageResourceInfo]:
    return read_array(x, read_damage_resource_info)


# Requirement

def read_individual_requirement(x, resource_database: ResourceDatabase) -> IndividualRequirement:
    requirement_type = ResourceType(read_byte(x))
    requirement_index = read_byte(x)
    amount = read_short(x)
    negate = read_bool(x)
    return IndividualRequirement.with_data(resource_database, requirement_type, requirement_index, amount,
                                           negate)


def read_requirement_list(x, resource_database: ResourceDatabase) -> List[IndividualRequirement]:
    return read_array(x, partial(read_individual_requirement, resource_database=resource_database))


def read_requirement_set(x, resource_database: ResourceDatabase) -> RequirementSet:
    return RequirementSet(read_array(x, partial(read_requirement_list, resource_database=resource_database)))


# Dock Weakness

def read_dock_weakness_database(x, resource_database: ResourceDatabase) -> DockWeaknessDatabase:
    def read_dock_weakness(x) -> DockWeakness:
        index = read_byte(x)
        name = read_string(x)
        requirement_set = read_requirement_set(x, resource_database)
        return DockWeakness(index, name, False, requirement_set)

    door_types = read_array(x, read_dock_weakness)
    portal_types = read_array(x, read_dock_weakness)
    return DockWeaknessDatabase(
        door=door_types,
        morph_ball=[DockWeakness(0, "Morph Ball Door", False, RequirementSet([[]]))],
        other=[DockWeakness(0, "Other Door", False, RequirementSet([[]]))],
        portal=portal_types
    )


class WorldReader:
    resource_database: ResourceDatabase
    dock_weakness_database: DockWeaknessDatabase

    def __init__(self, resource_database: ResourceDatabase, dock_weakness_database: DockWeaknessDatabase):
        self.resource_database = resource_database
        self.dock_weakness_database = dock_weakness_database

    def read_node(self, x) -> Node:
        name = read_string(x)
        heal = read_bool(x)
        node_type = read_byte(x)

        if node_type == 0:
            x.read(2)  # Throw 2 bytes away
            return GenericNode(name, heal)

        elif node_type == 1:
            dock_index = read_byte(x)
            connected_area_asset_id = read_uint(x)
            connected_dock_index = read_byte(x)
            dock_type = DockType(read_byte(x))
            dock_weakness_index = read_byte(x)
            x.read(5)  # Throw 5 bytes away
            return DockNode(name, heal, dock_index, connected_area_asset_id, connected_dock_index,
                            self.dock_weakness_database.get_by_type_and_index(dock_type, dock_weakness_index))

        elif node_type == 2:
            pickup_index = read_byte(x)
            x.read(2)  # Throw 2 bytes away
            return PickupNode(name, heal, pickup_index)

        elif node_type == 3:
            destination_world_asset_id = read_uint(x)
            destination_area_asset_id = read_uint(x)
            teleporter_instance_id = read_uint(x)
            x.read(2)  # Throw 2 bytes away
            return TeleporterNode(name, heal, destination_world_asset_id, destination_area_asset_id,
                                  teleporter_instance_id)

        elif node_type == 4:
            event_index = read_byte(x)
            x.read(2)  # Throw 2 bytes away
            return EventNode(name, heal, event_index)

        else:
            raise Exception("Unknown node type: {}".format(node_type))

    def read_area(self, x) -> Area:
        name = read_string(x)
        asset_id = read_uint(x)
        node_count = read_byte(x)
        default_node_index = read_byte(x)
        nodes = [
            self.read_node(x)
            for _ in range(node_count)
        ]
        connections = {
            source: {
                target: read_requirement_set(x, self.resource_database)
                for target in range(node_count)
                if source != target
            }
            for source in range(node_count)
        }
        return Area(name, asset_id, default_node_index, nodes, connections)

    def read_area_list(self, x) -> List[Area]:
        return read_array(x, self.read_area)

    def read_world(self, x) -> World:
        name = read_string(x)
        asset_id = read_uint(x)
        areas = self.read_area_list(x)
        return World(name, asset_id, areas)

    def read_world_list(self, x) -> List[World]:
        return read_array(x, self.read_world)


def parse_file(x) -> RandomizerFileData:
    if x.read(4) != b"Req.":
        raise Exception("Invalid file format.")

    format_version = read_uint(x)
    if format_version != 5:
        raise Exception("Unsupported format version: {}, expected 5".format(format_version))

    game = read_byte(x)
    game_name = read_string(x)

    items = read_resource_info_array(x)
    events = read_resource_info_array(x)
    tricks = read_resource_info_array(x)
    damage = read_damage_resource_info_array(x)
    misc = read_resource_info_array(x)
    # File seems to have a mistake here: no count for difficulty.
    difficulty = [SimpleResourceInfo(read_byte(x), read_string(x), read_string(x))]
    versions = read_resource_info_array(x)

    resource_database = ResourceDatabase(item=items, event=events, trick=tricks, damage=damage, version=versions,
                                         misc=misc, difficulty=difficulty)

    dock_weakness_database = read_dock_weakness_database(x, resource_database)
    world_reader = WorldReader(resource_database, dock_weakness_database)
    worlds = world_reader.read_world_list(x)

    return RandomizerFileData(
        game=game,
        game_name=game_name,
        resource_database=resource_database,
        dock_weakness_database=dock_weakness_database,
        worlds=worlds
    )


def read(path):
    with open(path, "rb") as x:
        return parse_file(x)


def main(path):
    data = read(path)
    world = data.worlds[1]
    import pprint

    for i in range(5):
        area = world.areas[i]
        print(area.name)
        pprint.pprint(area.nodes)
        print()


if __name__ == "__main__":
    import sys

    main(sys.argv[1])
