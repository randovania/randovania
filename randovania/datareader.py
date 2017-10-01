import pprint
import struct
from typing import List

from randovania.game_description import DamageReduction, SimpleRequirementInfo, DamageRequirementInfo, \
    IndividualRequirement, \
    DockWeakness, RequirementSet, World, Area, Node, GenericNode, DockNode, PickupNode, TeleporterNode, EventNode, \
    RandomizerFileData, RequirementType, RequirementInfoDatabase


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


def read_requirement_info(x) -> SimpleRequirementInfo:
    index = read_byte(x)
    long_name = read_string(x)
    short_name = read_string(x)
    return SimpleRequirementInfo(index, long_name, short_name)


def read_requirement_info_array(x) -> List[SimpleRequirementInfo]:
    return read_array(x, read_requirement_info)


def read_damagerequirement_info(x) -> DamageRequirementInfo:
    index = read_byte(x)
    long_name = read_string(x)
    short_name = read_string(x)
    return DamageRequirementInfo(index, long_name, short_name, read_damage_reductions(x))


def read_damagerequirement_info_array(x) -> List[DamageRequirementInfo]:
    return read_array(x, read_damagerequirement_info)


def read_node(x) -> Node:
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
        dock_type = read_byte(x)
        dock_weakness_index = read_byte(x)
        x.read(5)  # Throw 5 bytes away
        return DockNode(name, heal, dock_index, connected_area_asset_id, connected_dock_index, dock_type,
                        dock_weakness_index)

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


class RequirementSetReader:
    database: RequirementInfoDatabase

    def __init__(self, database: RequirementInfoDatabase):
        self.database = database

    def read_individual_requirement(self, x) -> IndividualRequirement:
        requirement_type = RequirementType(read_byte(x))
        requirement_index = read_byte(x)
        amount = read_short(x)
        negate = read_bool(x)
        return IndividualRequirement.with_data(self.database, requirement_type, requirement_index, amount, negate)

    def read_requirement_list(self, x) -> List[IndividualRequirement]:
        return read_array(x, self.read_individual_requirement)

    def read_requirement_set(self, x) -> RequirementSet:
        return RequirementSet(read_array(x, self.read_requirement_list))

    def read_dock_weakness(self, x) -> DockWeakness:
        index = read_byte(x)
        name = read_string(x)
        requirement_set = self.read_requirement_set(x)
        return DockWeakness(index, name, False, requirement_set)

    def read_dock_weakness_list(self, x) -> List[DockWeakness]:
        return read_array(x, self.read_dock_weakness)

    def read_area(self, x) -> Area:
        name = read_string(x)
        asset_id = read_uint(x)
        node_count = read_byte(x)
        default_node_index = read_byte(x)
        nodes = [
            read_node(x)
            for _ in range(node_count)
        ]
        connections = {
            source: {
                target: self.read_requirement_set(x)
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

    items = read_requirement_info_array(x)
    events = read_requirement_info_array(x)
    tricks = read_requirement_info_array(x)
    damage = read_damagerequirement_info_array(x)
    misc = read_requirement_info_array(x)

    # File seems to have a mistake here.
    difficulty = [SimpleRequirementInfo(read_byte(x), read_string(x), read_string(x))]

    versions = read_requirement_info_array(x)

    pprint.pprint(versions)

    database = RequirementInfoDatabase(item=items, event=events, trick=tricks, damage=damage, version=versions,
                                       misc=misc, difficulty=difficulty)

    reader = RequirementSetReader(database)
    door_types = reader.read_dock_weakness_list(x)
    portal_types = reader.read_dock_weakness_list(x)
    worlds = reader.read_world_list(x)

    return RandomizerFileData(
        game=game,
        game_name=game_name,
        database=database,
        door_dock_weakness=door_types,
        portal_dock_weakness=portal_types,
        worlds=worlds
    )


def read(path):
    with open(path, "rb") as x:
        return parse_file(x)


def main(path):
    data = read(path)
    world = data.worlds[0]
    area = world.areas[0]
    import pprint
    print(area.name)
    pprint.pprint(area.nodes)
    pprint.pprint(area.connections)


if __name__ == "__main__":
    import sys

    main(sys.argv[1])
