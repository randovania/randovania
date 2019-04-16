import copy
import functools
import json
import operator
from pathlib import Path
from typing import TypeVar, BinaryIO, Dict, TextIO

import construct
from construct import Struct, Int32ub, Const, CString, Byte, Rebuild, Embedded, Float32b, Flag, \
    Short, PrefixedArray, Array, Switch

X = TypeVar('X')
current_format_version = 6

_IMPOSSIBLE_SET = [[{'requirement_type': 5, 'requirement_index': 1, 'amount': 1, 'negate': False}]]

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


def _convert_to_raw_python(value):
    if isinstance(value, construct.ListContainer):
        return [
            _convert_to_raw_python(item)
            for item in value
        ]

    if isinstance(value, construct.Container):
        return {
            key: _convert_to_raw_python(item)
            for key, item in value.items()
            if not key.startswith("_")
        }

    return value


def decode(binary_io: BinaryIO, extra_io: TextIO) -> Dict:
    decoded = _convert_to_raw_python(ConstructGame.parse_stream(binary_io))
    extra = json.load(extra_io)

    for world in decoded["worlds"]:
        for area in world["areas"]:

            for node in area["nodes"]:
                data = node.pop("data")
                if data is not None:
                    for key, value in data.items():
                        node[key] = value
                node["connections"] = {}

            for i, connections in enumerate(area.pop("connections")):
                node = area["nodes"][i]

                j = 0
                for connection in connections:
                    if j == i:
                        j += 1

                    if connection != _IMPOSSIBLE_SET:
                        node["connections"][area["nodes"][j]["name"]] = list(sorted(connection,
                                                                                    key=sort_requirement_list))
                    j += 1

    return {
        "game": decoded["game"],
        "game_name": decoded["game_name"],
        "resource_database": decoded["resource_database"],
        "starting_location": extra["starting_location"],
        "initial_states": extra["initial_states"],
        "victory_condition": extra["victory_condition"],
        "dock_weakness_database": decoded["dock_weakness_database"],
        "worlds": decoded["worlds"],
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
            5: Struct(
                gate_index=Byte,
            ),
            6: Struct(
                string_asset_id=Int32ub,
                lore_type=Byte,
                extra=Byte,
            )
        }
    )
)

ConstructArea = Struct(
    name=CString("utf8"),
    asset_id=Int32ub,
    _node_count=Rebuild(Byte, lambda this: len(this.nodes)),
    default_node_index=Byte,
    nodes=Array(lambda this: this._node_count, ConstructNode),
    connections=Array(
        lambda this: this._node_count,
        Array(lambda this: this._node_count - 1, ConstructRequirementSet)
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
