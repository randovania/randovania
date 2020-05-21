import copy
import functools
import operator
from pathlib import Path
from typing import TypeVar, BinaryIO, Dict, Any

import construct
from construct import Struct, Int32ub, Const, CString, Byte, Rebuild, Embedded, Float32b, Flag, \
    Short, PrefixedArray, Array, Switch, If

from randovania.game_description.node import LoreType

X = TypeVar('X')
current_format_version = 7

_IMPOSSIBLE_SET = {"type": "or", "data": []}

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


def _convert_to_raw_python(value) -> Any:
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

    if isinstance(value, construct.EnumIntegerString):
        return str(value)

    return value


def decode(binary_io: BinaryIO) -> Dict:
    decoded = _convert_to_raw_python(ConstructGame.parse_stream(binary_io))

    decoded.pop("format_version")
    decoded.pop("magic_number")
    decoded["initial_states"] = dict(decoded["initial_states"])

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
                        node["connections"][area["nodes"][j]["name"]] = connection
                        # node["connections"][area["nodes"][j]["name"]] = list(sorted(connection,
                        #                                                             key=sort_requirement_list))
                    j += 1

    fields = [
        "game",
        "game_name",
        "resource_database",
        "game_specific",
        "starting_location",
        "initial_states",
        "victory_condition",
        "dock_weakness_database",
        "worlds",
    ]
    result = {
        field_name: decoded.pop(field_name)
        for field_name in fields
    }
    if decoded:
        raise ValueError(f"Unexpected fields remaining in data: {list(decoded.keys())}")

    return result


def decode_file_path(binary_file_path: Path) -> Dict:
    with binary_file_path.open("rb") as binary_io:
        return decode(binary_io)


def encode(original_data: Dict, x: BinaryIO) -> None:
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

    data["initial_states"] = list(data["initial_states"].items())

    ConstructGame.build_stream(data, x)

    # Resource Info database
    data.pop("game")
    data.pop("game_name")
    data.pop("resource_database")
    data.pop("game_specific")
    data.pop("dock_weakness_database")
    data.pop("worlds")
    data.pop("victory_condition")
    data.pop("starting_location")
    data.pop("initial_states")

    if data:
        raise ValueError(f"Unexpected fields remaining in data: {list(data.keys())}")


ConstructResourceInfo = Struct(
    index=Byte,
    long_name=CString("utf8"),
    short_name=CString("utf8"),
)

ConstructResourceRequirement = Struct(
    type=Byte,
    index=Byte,
    amount=Short,
    negate=Flag,
)

requirement_type_map = {
    "resource": ConstructResourceRequirement,
}

ConstructRequirement = Struct(
    type=construct.Enum(Byte, resource=0, **{"and": 1, "or": 2}),
    data=Switch(lambda this: this.type, requirement_type_map)
)
requirement_type_map["and"] = PrefixedArray(Byte, ConstructRequirement)
requirement_type_map["or"] = PrefixedArray(Byte, ConstructRequirement)

ConstructDockWeakness = Struct(
    index=Byte,
    name=CString("utf8"),
    is_blast_door=Flag,
    requirement=ConstructRequirement,
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

ConstructEchoesBeamConfiguration = Struct(
    item_index=Byte,
    _has_ammo_a=Rebuild(Flag, lambda this: this.ammo_a is not None),
    ammo_a=If(lambda this: this._has_ammo_a, Byte),
    _has_ammo_b=Rebuild(Flag, lambda this: this.ammo_b is not None),
    ammo_b=If(lambda this: this._has_ammo_b, Byte),
    uncharged_cost=Byte,
    charged_cost=Byte,
    combo_missile_cost=Byte,
    combo_ammo_cost=Byte,
)

ConstructEchoesGameSpecific = Struct(
    energy_per_tank=Float32b,
    beam_configurations=PrefixedArray(Byte, ConstructEchoesBeamConfiguration),
)

ConstructResourceGain = Struct(
    resource_type=Byte,
    resource_index=Byte,
    amount=Short,
)

ConstructLoreType = construct.Enum(Byte, **{lore_type.value: i for i, lore_type in enumerate(LoreType)})

ConstructNode = Struct(
    name=CString("utf8"),
    heal=Flag,
    node_type=construct.Enum(Byte, generic=0, dock=1, pickup=2, teleporter=3, event=4, translator_gate=5, logbook=6),
    data=Switch(
        lambda this: this.node_type,
        {
            "dock": Struct(
                dock_index=Byte,
                connected_area_asset_id=Int32ub,
                connected_dock_index=Byte,
                dock_type=Byte,
                dock_weakness_index=Byte,
                _=Const(b"\x00\x00\x00"),
            ),
            "pickup": Struct(
                pickup_index=Byte,
                major_location=Flag,
            ),
            "teleporter": Struct(
                destination_world_asset_id=Int32ub,
                destination_area_asset_id=Int32ub,
                teleporter_instance_id=Int32ub,
                _has_scan_asset_id=Rebuild(Flag, lambda this: this.scan_asset_id is not None),
                scan_asset_id=If(lambda this: this._has_scan_asset_id, Int32ub),
                keep_name_when_vanilla=Flag,
                editable=Flag,
            ),
            "event": Struct(
                event_index=Byte,
            ),
            "translator_gate": Struct(
                gate_index=Byte,
            ),
            "logbook": Struct(
                string_asset_id=Int32ub,
                lore_type=ConstructLoreType,
                extra=Byte,
            )
        }
    )
)

ConstructArea = Struct(
    name=CString("utf8"),
    in_dark_aether=Flag,
    asset_id=Int32ub,
    _node_count=Rebuild(Byte, lambda this: len(this.nodes)),
    default_node_index=Byte,
    nodes=Array(lambda this: this._node_count, ConstructNode),
    connections=Array(
        lambda this: this._node_count,
        Array(lambda this: this._node_count - 1, ConstructRequirement)
    )
)

ConstructWorld = Struct(
    name=CString("utf8"),
    dark_name=CString("utf8"),
    asset_id=Int32ub,
    areas=PrefixedArray(Byte, ConstructArea),
)

ConstructGame = Struct(
    magic_number=Const(b"Req."),
    format_version=Const(current_format_version, Int32ub),
    game=Byte,
    game_name=CString("utf8"),
    resource_database=ConstructResourceDatabase,
    game_specific=ConstructEchoesGameSpecific,
    dock_weakness_database=Struct(
        door=PrefixedArray(Byte, ConstructDockWeakness),
        portal=PrefixedArray(Byte, ConstructDockWeakness),
    ),
    victory_condition=ConstructRequirement,
    starting_location=Struct(
        world_asset_id=Int32ub,
        area_asset_id=Int32ub,
    ),
    initial_states=PrefixedArray(Byte, construct.Sequence(CString("utf8"), PrefixedArray(Byte, ConstructResourceGain))),
    worlds=PrefixedArray(Byte, ConstructWorld),
)
