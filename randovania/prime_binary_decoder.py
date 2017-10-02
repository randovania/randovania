from typing import List, Callable, TypeVar, BinaryIO, Dict

from randovania.binary_source import BinarySource

X = TypeVar('X')


def read_array(source: BinarySource, item_reader: Callable[[BinarySource], X]) -> List[X]:
    count = source.read_byte()
    return [
        item_reader(source)
        for _ in range(count)
    ]


def read_damage_reduction(source: BinarySource) -> Dict:
    return {
        "index": source.read_byte(),
        "multiplier": source.read_float(),
    }


def read_damage_reductions(source: BinarySource) -> List[Dict]:
    return read_array(source, read_damage_reduction)


def read_resource_info(source: BinarySource) -> Dict:
    return {
        "index": source.read_byte(),
        "long_name": source.read_string(),
        "short_name": source.read_string(),
    }


def read_resource_info_array(source: BinarySource) -> List[Dict]:
    return read_array(source, read_resource_info)


def read_damage_resource_info(source: BinarySource) -> Dict:
    return {
        "index": source.read_byte(),
        "long_name": source.read_string(),
        "short_name": source.read_string(),
        "reductions": read_damage_reductions(source),
    }


def read_damage_resource_info_array(source: BinarySource) -> List[Dict]:
    return read_array(source, read_damage_resource_info)


# Requirement

def read_individual_requirement(source: BinarySource) -> Dict:
    return {
        "requirement_type": source.read_byte(),
        "requirement_index": source.read_byte(),
        "amount": source.read_short(),
        "negate": source.read_bool(),
    }


def read_requirement_list(source: BinarySource) -> List[Dict]:
    return read_array(source, read_individual_requirement)


def read_requirement_set(source: BinarySource) -> List[List[Dict]]:
    return read_array(source, read_requirement_list)


# Dock Weakness

def read_dock_weakness_database(source: BinarySource) -> Dict:
    def read_dock_weakness(source: BinarySource) -> Dict:
        return {
            "index": source.read_byte(),
            "name": source.read_string(),
            "is_blast_door": source.read_bool(),
            "requirement_set": read_requirement_set(source),
        }

    return {
        "door": read_array(source, read_dock_weakness),
        "portal": read_array(source, read_dock_weakness),
    }


def read_node(source: BinarySource) -> Dict:
    node = {
        "name": source.read_string(),
        "heal": source.read_bool(),
        "node_type": source.read_byte(),
    }
    node_type = node["node_type"]

    if node_type == 0:
        pass

    elif node_type == 1:
        node["dock_index"] = source.read_byte()
        node["connected_area_asset_id"] = source.read_uint()
        node["connected_dock_index"] = source.read_byte()
        node["dock_type"] = source.read_byte()
        node["dock_weakness_index"] = source.read_byte()
        source.skip(3)

    elif node_type == 2:
        node["pickup_index"] = source.read_byte()

    elif node_type == 3:
        node["destination_world_asset_id"] = source.read_uint()
        node["destination_area_asset_id"] = source.read_uint()
        node["teleporter_instance_id"] = source.read_uint()

    elif node_type == 4:
        node["event_index"] = source.read_byte()

    else:
        raise Exception("Unknown node type: {}".format(node_type))

    return node


def read_area(source: BinarySource) -> Dict:
    name = source.read_string()
    asset_id = source.read_uint()
    node_count = source.read_byte()
    default_node_index = source.read_byte()

    # TODO: hardcoded data fix
    # Aerie Transport Station has default_node_index not set
    if asset_id == 3136899603:
        default_node_index = 2

    nodes = [
        read_node(source)
        for _ in range(node_count)
    ]

    connections = [
        [
            read_requirement_set(source) if origin != target else None
            for target in range(node_count)
        ]
        for origin in range(node_count)
    ]
    # TODO: hardcoded data fix
    # Hive Temple Access has incorrect requirements for unlocking Hive Temple gate
    if asset_id == 3968294891:
        connections[1][2] = [[
            {
                "requirement_type": 0,
                "requirement_index": 38 + i,
                "amount": 1,
                "negate": False,
            }
            for i in range(3)
        ]]
    return {
        "name": name,
        "asset_id": asset_id,
        "default_node_index": default_node_index,
        "nodes": nodes,
        "connections": connections,
    }


def read_area_list(source: BinarySource) -> List[Dict]:
    return read_array(source, read_area)


def read_world(source: BinarySource) -> Dict:
    return {
        "name": source.read_string(),
        "asset_id": source.read_uint(),
        "areas": read_area_list(source),
    }


def read_world_list(source: BinarySource) -> List[Dict]:
    return read_array(source, read_world)


def decode(x: BinaryIO) -> Dict:
    if x.read(4) != b"Req.":
        raise Exception("Invalid file format.")

    source = BinarySource(x)

    format_version = source.read_uint()
    if format_version != 6:
        raise Exception("Unsupported format version: {}, expected 6".format(format_version))

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

    dock_weakness_database = read_dock_weakness_database(source)
    worlds = read_world_list(source)

    return {
        "game": game,
        "game_name": game_name,
        "resource_database": {
            "items": items,
            "events": events,
            "tricks": tricks,
            "damage": damage,
            "versions": versions,
            "misc": misc,
            "difficulty": difficulty,
        },
        "dock_weakness_database": dock_weakness_database,
        "worlds": worlds,
    }


def decode_filepath(path) -> Dict:
    with open(path, "rb") as x:  # type: BinaryIO
        return decode(x)
