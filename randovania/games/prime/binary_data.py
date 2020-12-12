import copy
from pathlib import Path
from typing import TypeVar, BinaryIO, Dict, Any

import construct
from construct import Struct, Int32ub, Const, CString, Byte, Rebuild, Embedded, Float32b, Flag, \
    Short, PrefixedArray, Array, Switch, If, VarInt, Sequence, Float64b, Pass

from randovania.game_description.node import LoreType
from randovania.games.game import RandovaniaGame

X = TypeVar('X')
current_format_version = 8

_IMPOSSIBLE_SET = {"type": "or", "data": []}


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
    decoded["resource_database"]["requirement_template"] = dict(decoded["resource_database"]["requirement_template"])

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
                    j += 1

    fields = [
        "game",
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
                    "coordinates": node.pop("coordinates"),
                    "node_type": node.pop("node_type"),
                    "data": node,
                }

    data["resource_database"]["requirement_template"] = list(data["resource_database"]["requirement_template"].items())
    data["initial_states"] = list(data["initial_states"].items())

    ConstructGame.build_stream(data, x)

    # Resource Info database
    data.pop("game")
    data.pop("resource_database")
    data.pop("game_specific")
    data.pop("dock_weakness_database")
    data.pop("worlds")
    data.pop("victory_condition")
    data.pop("starting_location")
    data.pop("initial_states")

    if data:
        raise ValueError(f"Unexpected fields remaining in data: {list(data.keys())}")


def OptionalValue(subcon):
    return construct.FocusedSeq(
        "value",
        present=Rebuild(Flag, construct.this.value != None),
        value=If(construct.this.present, subcon),
    )


ConstructResourceInfo = Struct(
    index=VarInt,
    long_name=CString("utf8"),
    short_name=CString("utf8"),
)

ConstructItemResourceInfo = Struct(
    index=VarInt,
    long_name=CString("utf8"),
    short_name=CString("utf8"),
    max_capacity=Int32ub,
    extra=OptionalValue(Int32ub),
)

ConstructTrickResourceInfo = Struct(
    index=VarInt,
    long_name=CString("utf8"),
    short_name=CString("utf8"),
    description=CString("utf8"),
)

ConstructResourceRequirement = Struct(
    type=Byte,
    index=VarInt,
    amount=Short,
    negate=Flag,
)

requirement_type_map = {
    "resource": ConstructResourceRequirement,
    "template": CString("utf8"),
}

ConstructRequirement = Struct(
    type=construct.Enum(Byte, resource=0, **{"and": 1, "or": 2}, template=3),
    data=Switch(lambda this: this.type, requirement_type_map)
)
requirement_type_map["and"] = PrefixedArray(VarInt, ConstructRequirement)
requirement_type_map["or"] = PrefixedArray(VarInt, ConstructRequirement)

ConstructDockWeakness = Struct(
    index=VarInt,
    name=CString("utf8"),
    is_blast_door=Flag,
    requirement=ConstructRequirement,
)

ConstructResourceDatabase = Struct(
    items=PrefixedArray(VarInt, ConstructItemResourceInfo),
    energy_tank_item_index=VarInt,
    item_percentage_index=VarInt,
    multiworld_magic_item_index=VarInt,
    events=PrefixedArray(VarInt, ConstructResourceInfo),
    tricks=PrefixedArray(VarInt, ConstructTrickResourceInfo),
    damage=PrefixedArray(VarInt, Struct(
        Embedded(ConstructResourceInfo),
        reductions=PrefixedArray(VarInt, Struct(
            index=VarInt,
            multiplier=Float32b,
        )),
    )),
    versions=PrefixedArray(VarInt, ConstructResourceInfo),
    misc=PrefixedArray(VarInt, ConstructResourceInfo),
    requirement_template=PrefixedArray(VarInt, Sequence(CString("utf8"), ConstructRequirement))
)

ConstructEchoesBeamConfiguration = Struct(
    item_index=VarInt,
    ammo_a=OptionalValue(Byte),
    ammo_b=OptionalValue(Byte),
    uncharged_cost=Byte,
    charged_cost=Byte,
    combo_missile_cost=Byte,
    combo_ammo_cost=Byte,
)

ConstructEchoesGameSpecific = Struct(
    energy_per_tank=Float32b,
    safe_zone_heal_per_second=Float32b,
    beam_configurations=PrefixedArray(VarInt, ConstructEchoesBeamConfiguration),
    dangerous_energy_tank=Flag,
)

ConstructResourceGain = Struct(
    resource_type=Byte,
    resource_index=VarInt,
    amount=VarInt,
)

ConstructLoreType = construct.Enum(Byte, **{lore_type.value: i for i, lore_type in enumerate(LoreType)})

ConstructNodeCoordinates = Struct(
    x=Float64b,
    y=Float64b,
    z=Float64b,
)

ConstructNode = Struct(
    name=CString("utf8"),
    heal=Flag,
    coordinates=OptionalValue(ConstructNodeCoordinates),
    node_type=construct.Enum(Byte, generic=0, dock=1, pickup=2, teleporter=3, event=4, translator_gate=5,
                             logbook=6, player_ship=7),
    data=Switch(
        lambda this: this.node_type,
        {
            "dock": Struct(
                dock_index=Byte,
                connected_area_asset_id=VarInt,
                connected_dock_index=Byte,
                dock_type=Byte,
                dock_weakness_index=VarInt,
                _=Const(b"\x00\x00\x00"),
            ),
            "pickup": Struct(
                pickup_index=VarInt,
                major_location=Flag,
            ),
            "teleporter": Struct(
                destination_world_asset_id=VarInt,
                destination_area_asset_id=VarInt,
                teleporter_instance_id=OptionalValue(VarInt),
                scan_asset_id=OptionalValue(VarInt),
                keep_name_when_vanilla=Flag,
                editable=Flag,
            ),
            "event": Struct(
                event_index=VarInt,
            ),
            "translator_gate": Struct(
                gate_index=VarInt,
            ),
            "logbook": Struct(
                string_asset_id=VarInt,
                lore_type=ConstructLoreType,
                extra=VarInt,
            ),
            "player_ship": Struct(
                is_unlocked=ConstructRequirement,
            )
        }
    )
)

ConstructArea = Struct(
    name=CString("utf8"),
    in_dark_aether=Flag,
    asset_id=VarInt,
    _node_count=Rebuild(VarInt, construct.len_(construct.this.nodes)),
    default_node_index=OptionalValue(VarInt),
    valid_starting_location=Flag,
    nodes=Array(lambda this: this._node_count, ConstructNode),
    connections=Array(
        lambda this: this._node_count,
        Array(lambda this: this._node_count - 1, ConstructRequirement)
    )
)

ConstructWorld = Struct(
    name=CString("utf8"),
    dark_name=OptionalValue(CString("utf8")),
    asset_id=VarInt,
    areas=PrefixedArray(VarInt, ConstructArea),
)

ConstructGameEnum = construct.Enum(Byte, **{enum_item.value: i for i, enum_item in enumerate(RandovaniaGame)})

game_specific_map = {
    RandovaniaGame.PRIME1.value: Struct(),
    RandovaniaGame.PRIME2.value: ConstructEchoesGameSpecific,
    RandovaniaGame.PRIME3.value: Struct(),
}

ConstructGame = Struct(
    magic_number=Const(b"Req."),
    format_version=Const(current_format_version, Int32ub),
    game=ConstructGameEnum,
    resource_database=ConstructResourceDatabase,
    game_specific=Switch(lambda this: this.game, game_specific_map),
    dock_weakness_database=Struct(
        door=PrefixedArray(VarInt, ConstructDockWeakness),
        portal=PrefixedArray(VarInt, ConstructDockWeakness),
        morph_ball=PrefixedArray(VarInt, ConstructDockWeakness),
    ),
    victory_condition=ConstructRequirement,
    starting_location=Struct(
        world_asset_id=VarInt,
        area_asset_id=VarInt,
    ),
    initial_states=PrefixedArray(VarInt, construct.Sequence(CString("utf8"),
                                                            PrefixedArray(VarInt, ConstructResourceGain))),
    worlds=PrefixedArray(VarInt, ConstructWorld),
)
