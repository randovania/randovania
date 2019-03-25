import copy
import functools
import json
import operator
import pprint
from pathlib import Path
from typing import List, Callable, TypeVar, BinaryIO, Dict, TextIO

from construct import Struct, Int32ub, Const, CString, Byte, Rebuild, Embedded, Float32b, Flag, \
    Short, PrefixedArray, Array, Switch, LazyStruct

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


def encode(original_data: Dict, x: BinaryIO) -> dict:
    data = copy.deepcopy(original_data)

    for world in data["worlds"]:
        for area in world["areas"]:
            area["connections"] = [
                [
                    origin["connections"].get(target["name"], _IMPOSSIBLE_SET)
                    for target in area["nodes"]
                    if origin != target
                ]
                for origin in area["nodes"]
            ]

            for i, node in enumerate(area["nodes"]):
                node.pop("connections")
                area["nodes"][i] = {
                    "name": node.pop("name"),
                    "heal": node.pop("heal"),
                    "node_type": node.pop("node_type"),
                    "data": node,
                }

    ConstructGame.build_stream(data, x)

    # Resource Info database
    data.pop("game")
    data.pop("game_name")
    data.pop("resource_database")
    data.pop("dock_weakness_database")
    data.pop("worlds")

    return data


ConstructResourceInfo = Struct(
    index=Byte,
    long_name=CString("utf8"),
    short_name=CString("utf8"),
)

ConstructIndividualRequirement = Struct(
    requirement_type=Byte,
    requirement_index=Byte,
    amount=Short,
    negate=Flag,
)
ConstructRequirementList = PrefixedArray(Byte, ConstructIndividualRequirement)
ConstructRequirementSet = PrefixedArray(Byte, ConstructRequirementList)

ConstructDockWeakness = Struct(
    index=Byte,
    name=CString("utf8"),
    is_blast_door=Flag,
    requirement_set=ConstructRequirementSet,
)

ConstructResourceDatabase = Struct(
    items=PrefixedArray(Byte, ConstructResourceInfo),
    events=PrefixedArray(Byte, ConstructResourceInfo),
    tricks=PrefixedArray(Byte, ConstructResourceInfo),
    damage=PrefixedArray(Byte, Struct(
        Embedded(ConstructResourceInfo),
        reductions=PrefixedArray(Byte, Struct(
            index=Byte,
            multiplier=Float32b,
        )),
    )),
    versions=PrefixedArray(Byte, ConstructResourceInfo),
    misc=PrefixedArray(Byte, ConstructResourceInfo),
    difficulty=PrefixedArray(Byte, ConstructResourceInfo),
)

ConstructNode = Struct(
    name=CString("utf8"),
    heal=Flag,
    node_type=Byte,
    data=Switch(
        lambda this: this.node_type,
        {
            1: Struct(
                dock_index=Byte,
                connected_area_asset_id=Int32ub,
                connected_dock_index=Byte,
                dock_type=Byte,
                dock_weakness_index=Byte,
                _=Const(b"\x00\x00\x00"),
            ),
            2: Struct(
                pickup_index=Byte,
            ),
            3: Struct(
                destination_world_asset_id=Int32ub,
                destination_area_asset_id=Int32ub,
                teleporter_instance_id=Int32ub,
            ),
            4: Struct(
                event_index=Byte,
            ),
        }
    )
)


ConstructArea = Struct(
    name=CString("utf8"),
    asset_id=Int32ub,
    node_count=Rebuild(Byte, lambda this: len(this.nodes)),
    default_node_index=Byte,
    nodes=Array(lambda this: this.node_count, ConstructNode),
    connections=Array(
        lambda this: this.node_count,
        Array(lambda this: this.node_count - 1, ConstructRequirementSet)
    )
)

ConstructWorld = Struct(
    name=CString("utf8"),
    asset_id=Int32ub,
    areas=PrefixedArray(Byte, ConstructArea),
)

ConstructGame = Struct(
    magic_number=Const(b"Req."),
    format_version=Const(current_format_version, Int32ub),
    game=Byte,
    game_name=CString("utf8"),
    resource_database=ConstructResourceDatabase,
    dock_weakness_database=Struct(
        door=PrefixedArray(Byte, ConstructDockWeakness),
        portal=PrefixedArray(Byte, ConstructDockWeakness),
    ),
    worlds=PrefixedArray(Byte, ConstructWorld),
)
