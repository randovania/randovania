import copy
import functools
import json
import operator
from pathlib import Path
from typing import List, Callable, TypeVar, BinaryIO, Dict, TextIO

from randovania.binary_file import BinarySource, BinaryWriter

X = TypeVar('X')
current_format_version = 6

_IMPOSSIBLE_SET = [[{'requirement_type': 5, 'requirement_index': 1, 'amount': 1, 'negate': False}]]
_TRIVIAL_LIST = [{'requirement_type': 5, 'requirement_index': 0, 'amount': 1, 'negate': False}]


def read_array(source: BinarySource,
               item_reader: Callable[[BinarySource], X]) -> List[X]:
    count = source.read_byte()
    return [item_reader(source) for _ in range(count)]


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

sort_individual_requirement = operator.itemgetter("requirement_type", "requirement_index", "amount", "negate")


def sort_requirement_list(item: list):
    return functools.reduce(
        operator.add,
        [
            sort_individual_requirement(individual)
            for individual in item
        ],
        tuple())


def read_individual_requirement(source: BinarySource) -> Dict:
    return {
        "requirement_type": source.read_byte(),
        "requirement_index": source.read_byte(),
        "amount": source.read_short(),
        "negate": source.read_bool(),
    }


def read_requirement_list(source: BinarySource) -> List[Dict]:
    result = read_array(source, read_individual_requirement)
    if result == _TRIVIAL_LIST:
        return []
    else:
        return list(sorted(result, key=sort_individual_requirement))


def read_requirement_set(source: BinarySource) -> List[List[Dict]]:
    result = read_array(source, read_requirement_list)
    if result == _IMPOSSIBLE_SET:
        return []
    else:
        return list(sorted(result, key=sort_requirement_list))


# Dock Weakness


def read_dock_weakness_database(source: BinarySource) -> Dict:
    def read_dock_weakness(_source: BinarySource) -> Dict:
        return {
            "index": _source.read_byte(),
            "name": _source.read_string(),
            "is_blast_door": _source.read_bool(),
            "requirement_set": read_requirement_set(_source),
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

    nodes = [read_node(source) for _ in range(node_count)]

    for origin in nodes:
        origin["connections"] = {}
        for target in nodes:
            if origin != target:
                requirement_set = read_requirement_set(source)
                if requirement_set:
                    origin["connections"][target["name"]] = requirement_set

    return {
        "name": name,
        "asset_id": asset_id,
        "default_node_index": default_node_index,
        "nodes": nodes
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


def decode(binary_io: BinaryIO, extra_io: TextIO) -> Dict:
    if binary_io.read(4) != b"Req.":
        raise Exception("Invalid file format.")

    source = BinarySource(binary_io)
    extra = json.load(extra_io)

    format_version = source.read_uint()
    if format_version != current_format_version:
        raise Exception("Unsupported format version: {}, expected {}".format(
            format_version, current_format_version))

    game = source.read_byte()
    game_name = source.read_string()

    items = read_resource_info_array(source)
    events = read_resource_info_array(source)
    tricks = read_resource_info_array(source)
    damage = read_damage_resource_info_array(source)
    versions = read_resource_info_array(source)
    misc = read_resource_info_array(source)
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
        "starting_location": extra["starting_location"],
        "initial_states": extra["initial_states"],
        "victory_condition": extra["victory_condition"],
        "dock_weakness_database": dock_weakness_database,
        "worlds": worlds,
    }


def decode_file_path(binary_file_path: Path, extra_file_path: Path) -> Dict:
    with binary_file_path.open("rb") as binary_io:  # type: BinaryIO
        with extra_file_path.open("r") as extra:
            return decode(binary_io, extra)


def write_array(writer: BinaryWriter, array: List[X],
                item_writer: Callable[[BinaryWriter, X], None]):
    writer.write_byte(len(array))
    for item in array:
        item_writer(writer, item)


def write_resource_info(writer: BinaryWriter, item: Dict):
    writer.write_byte(item["index"])
    writer.write_string(item["long_name"])
    writer.write_string(item["short_name"])


def write_damage_reduction(writer: BinaryWriter, item: Dict):
    writer.write_byte(item["index"])
    writer.write_float(item["multiplier"])


def write_damage_resource_info(writer: BinaryWriter, item: Dict):
    write_resource_info(writer, item)
    write_array(writer, item["reductions"], write_damage_reduction)


def write_individual_requirement(writer: BinaryWriter, item: Dict):
    writer.write_byte(item["requirement_type"])
    writer.write_byte(item["requirement_index"])
    writer.write_short(item["amount"])
    writer.write_bool(item["negate"])


def write_requirement_set(writer: BinaryWriter, item: List[List[Dict]]):
    write_array(writer,
                item,
                lambda w, i: write_array(w, i, item_writer=write_individual_requirement))


def write_dock_weakness(writer: BinaryWriter, item: Dict):
    writer.write_byte(item["index"])
    writer.write_string(item["name"])
    writer.write_bool(item["is_blast_door"])
    write_requirement_set(writer, item["requirement_set"])


def write_node(writer: BinaryWriter, node: Dict):
    writer.write_string(node["name"])
    writer.write_bool(node["heal"])
    writer.write_byte(node["node_type"])

    node_type = node["node_type"]

    if node_type == 0:
        pass

    elif node_type == 1:
        writer.write_byte(node["dock_index"])
        writer.write_uint(node["connected_area_asset_id"])
        writer.write_byte(node["connected_dock_index"])
        writer.write_byte(node["dock_type"])
        writer.write_byte(node["dock_weakness_index"])
        writer.write_byte(0)
        writer.write_byte(0)
        writer.write_byte(0)

    elif node_type == 2:
        writer.write_byte(node["pickup_index"])

    elif node_type == 3:
        writer.write_uint(node["destination_world_asset_id"])
        writer.write_uint(node["destination_area_asset_id"])
        writer.write_uint(node["teleporter_instance_id"])

    elif node_type == 4:
        writer.write_byte(node["event_index"])

    else:
        raise Exception("Unknown node type: {}".format(node_type))


def write_area(writer: BinaryWriter, item: Dict):
    writer.write_string(item["name"])
    writer.write_uint(item["asset_id"])
    writer.write_byte(len(item["nodes"]))
    writer.write_byte(item["default_node_index"])
    for node in item["nodes"]:
        write_node(writer, node)

    for origin in item["nodes"]:
        for target in item["nodes"]:
            if origin != target:
                requirement_set = origin["connections"].get(target["name"], _IMPOSSIBLE_SET)
                write_requirement_set(writer, requirement_set)


def write_world(writer: BinaryWriter, item: Dict):
    writer.write_string(item["name"])
    writer.write_uint(item["asset_id"])
    write_array(writer, item["areas"], write_area)


def encode(original_data: Dict, x: BinaryIO) -> dict:
    data = copy.copy(original_data)

    writer = BinaryWriter(x)
    x.write(b"Req.")
    writer.write_uint(current_format_version)
    writer.write_byte(data.pop("game"))
    writer.write_string(data.pop("game_name"))

    # Resource Info database
    resource_database = data.pop("resource_database")
    write_array(writer, resource_database["items"], write_resource_info)
    write_array(writer, resource_database["events"], write_resource_info)
    write_array(writer, resource_database["tricks"], write_resource_info)
    write_array(writer, resource_database["damage"], write_damage_resource_info)
    write_array(writer, resource_database["versions"], write_resource_info)
    write_array(writer, resource_database["misc"], write_resource_info)
    write_array(writer, resource_database["difficulty"], write_resource_info)

    # Dock Weakness Database
    dock_weakness_database = data.pop("dock_weakness_database")
    write_array(writer, dock_weakness_database["door"], write_dock_weakness)
    write_array(writer, dock_weakness_database["portal"], write_dock_weakness)

    # Worlds List
    write_array(writer, data.pop("worlds"), write_world)

    return data
