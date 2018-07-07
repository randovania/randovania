import functools
import json
import os
from functools import partial
from typing import List, Callable, TypeVar, BinaryIO, Dict, TextIO

from randovania import get_data_path
from randovania.binary_file import BinarySource, BinaryWriter

X = TypeVar('X')
current_format_version = 6


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

    connections = [[
        read_requirement_set(source) if origin != target else None
        for target in range(node_count)
    ] for origin in range(node_count)]

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
            "pickups": extra["pickups"]
        },
        "starting_world_asset_id": extra["starting_world_asset_id"],
        "starting_area_asset_id": extra["starting_area_asset_id"],
        "starting_items": extra["starting_items"],
        "item_loss_items": extra["item_loss_items"],
        "victory_condition": extra["victory_condition"],
        "dock_weakness_database": dock_weakness_database,
        "worlds": worlds,
    }


def decode_file_path(binary_file_path: str, extra_file_path: str) -> Dict:
    with open(binary_file_path, "rb") as binary_io:  # type: BinaryIO
        with open(extra_file_path, "r") as extra:
            return decode(binary_io, extra)


def write_array(writer: BinaryWriter, array: List[X],
                item_writer: Callable[[BinaryWriter, X], None]):
    writer.write_byte(len(array))
    for item in array:
        item_writer(writer, item)


def encode(data: Dict, x: BinaryIO):
    writer = BinaryWriter(x)
    x.write(b"Req.")
    writer.write_uint(current_format_version)
    writer.write_byte(data["game"])
    writer.write_string(data["game_name"])

    def write_resource_info(_writer, item: Dict):
        _writer.write_byte(item["index"])
        _writer.write_string(item["long_name"])
        _writer.write_string(item["short_name"])

    def write_damage_reduction(_writer, item: Dict):
        _writer.write_byte(item["index"])
        _writer.write_float(item["multiplier"])

    def write_damage_resource_info(_writer, item: Dict):
        write_resource_info(_writer, item)
        write_array(_writer, item["reductions"], write_damage_reduction)

    def write_individual_requirement(_writer, item: Dict):
        _writer.write_byte(item["requirement_type"])
        _writer.write_byte(item["requirement_index"])
        _writer.write_short(item["amount"])
        _writer.write_bool(item["negate"])

    def write_requirement_set(_writer, item: List[List[Dict]]):
        write_array(_writer, item,
                    partial(
                        write_array, item_writer=write_individual_requirement))

    # Resource Info database
    write_array(writer, data["resource_database"]["items"],
                write_resource_info)
    write_array(writer, data["resource_database"]["events"],
                write_resource_info)
    write_array(writer, data["resource_database"]["tricks"],
                write_resource_info)
    write_array(writer, data["resource_database"]["damage"],
                write_damage_resource_info)
    write_array(writer, data["resource_database"]["versions"],
                write_resource_info)
    write_array(writer, data["resource_database"]["misc"], write_resource_info)
    write_array(writer, data["resource_database"]["difficulty"],
                write_resource_info)

    # Dock Weakness Database
    def write_dock_weakness(_writer, item: Dict):
        _writer.write_byte(item["index"])
        _writer.write_string(item["name"])
        _writer.write_bool(item["is_blast_door"])
        write_requirement_set(_writer, item["requirement_set"])

    write_array(writer, data["dock_weakness_database"]["door"],
                write_dock_weakness)
    write_array(writer, data["dock_weakness_database"]["portal"],
                write_dock_weakness)

    # Worlds List
    def write_node(_writer: BinaryWriter, node: Dict):
        _writer.write_string(node["name"])
        _writer.write_bool(node["heal"])
        _writer.write_byte(node["node_type"])

        node_type = node["node_type"]

        if node_type == 0:
            pass

        elif node_type == 1:
            _writer.write_byte(node["dock_index"])
            _writer.write_uint(node["connected_area_asset_id"])
            _writer.write_byte(node["connected_dock_index"])
            _writer.write_byte(node["dock_type"])
            _writer.write_byte(node["dock_weakness_index"])
            _writer.write_byte(0)
            _writer.write_byte(0)
            _writer.write_byte(0)

        elif node_type == 2:
            _writer.write_byte(node["pickup_index"])

        elif node_type == 3:
            _writer.write_uint(node["destination_world_asset_id"])
            _writer.write_uint(node["destination_area_asset_id"])
            _writer.write_uint(node["teleporter_instance_id"])

        elif node_type == 4:
            _writer.write_byte(node["event_index"])

        else:
            raise Exception("Unknown node type: {}".format(node_type))

    def write_area(_writer: BinaryWriter, item: Dict):
        _writer.write_string(item["name"])
        _writer.write_uint(item["asset_id"])
        _writer.write_byte(len(item["nodes"]))
        _writer.write_byte(item["default_node_index"])
        for node in item["nodes"]:
            write_node(_writer, node)

        for outer in item["connections"]:
            for inner in outer:
                if inner is not None:
                    write_requirement_set(_writer, inner)

    def write_world(_writer: BinaryWriter, item: Dict):
        _writer.write_string(item["name"])
        _writer.write_uint(item["asset_id"])
        write_array(_writer, item["areas"], write_area)

    write_array(writer, data["worlds"], write_world)


@functools.lru_cache()
def decode_default_prime2():
    return decode_file_path(
        os.path.join(get_data_path(), "prime2.bin"),
        os.path.join(get_data_path(), "prime2_extra.json")
    )
