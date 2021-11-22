import copy
import json
from pathlib import Path
from typing import TypeVar, BinaryIO, Dict, Any

import construct
from construct import (Struct, Int32ub, Const, CString, Byte, Rebuild, Float32b, Flag,
                       Short, PrefixedArray, Switch, If, VarInt, Float64b)

from randovania.game_description import schema_migration
from randovania.game_description.world.node import LoreType
from randovania.games.game import RandovaniaGame

X = TypeVar('X')
current_format_version = 9

String = CString("utf-8")


def convert_to_raw_python(value) -> Any:
    if isinstance(value, construct.ListContainer):
        return [
            convert_to_raw_python(item)
            for item in value
        ]

    if isinstance(value, construct.Container):
        return {
            key: convert_to_raw_python(item)
            for key, item in value.items()
            if not key.startswith("_")
        }

    if isinstance(value, construct.EnumIntegerString):
        return str(value)

    return value


def decode(binary_io: BinaryIO) -> Dict:
    decoded = convert_to_raw_python(ConstructGame.parse_stream(binary_io))
    decoded.pop("format_version")
    decoded.pop("magic_number")

    fields = [
        "schema_version",
        "game",
        "resource_database",
        "starting_location",
        "initial_states",
        "minimal_logic",
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
    ConstructGame.build_stream(data, x)

    # Resource Info database
    data.pop("schema_version")
    data.pop("game")
    data.pop("resource_database")
    data.pop("dock_weakness_database")
    data.pop("worlds")
    data.pop("victory_condition")
    data.pop("starting_location")
    data.pop("initial_states")
    data.pop("minimal_logic")

    if data:
        raise ValueError(f"Unexpected fields remaining in data: {list(data.keys())}")


def OptionalValue(subcon):
    return construct.FocusedSeq(
        "value",
        present=Rebuild(Flag, construct.this.value != None),
        value=If(construct.this.present, subcon),
    )


class DictAdapter(construct.Adapter):
    def _decode(self, obj: construct.ListContainer, context, path):
        result = construct.Container()
        last = {}
        for i, item in enumerate(obj):
            key = item.key
            if key in result:
                raise construct.ConstructError(f"Key {key} found twice in object", path)
            last[key] = i
            result[key] = item.value
        return result

    def _encode(self, obj: construct.Container, context, path):
        return construct.ListContainer(
            construct.Container(key=type_, value=item)
            for type_, item in obj.items()
        )


def ConstructDict(subcon):
    return DictAdapter(PrefixedArray(VarInt, Struct(
        key=String,
        value=subcon,
    )))


JsonEncodedValue = construct.ExprAdapter(
    String,
    # Decode
    lambda obj, ctx: json.loads(obj),
    # Encode
    lambda obj, ctx: json.dumps(obj),
)


def _build_resource_info(**kwargs):
    return Struct(
        long_name=String,
        **kwargs,
        extra=JsonEncodedValue,
    )


ConstructAreaIdentifier = construct.Struct(
    world_name=String,
    area_name=String,
)

ConstructNodeIdentifier = construct.Struct(
    world_name=String,
    area_name=String,
    node_name=String,
)

ConstructResourceInfo = _build_resource_info()

ConstructItemResourceInfo = _build_resource_info(
    max_capacity=Int32ub,
)

ConstructTrickResourceInfo = _build_resource_info(
    description=String,
)

ConstructDamageReductions = Struct(
    name=String,
    reductions=PrefixedArray(VarInt, Struct(
        name=String,
        multiplier=Float32b,
    ))
)

ConstructResourceType = construct.Enum(Byte, items=0, events=1, tricks=2, damage=3, versions=4, misc=5, pickup_index=7, gate_index=8, logbook_index=9, ship_node=10)

ConstructResourceRequirement = Struct(
    type=ConstructResourceType,
    name=String,
    amount=Short,
    negate=Flag,
)

requirement_type_map = {
    "resource": ConstructResourceRequirement,
    "template": String,
}

ConstructRequirement = Struct(
    type=construct.Enum(Byte, resource=0, **{"and": 1, "or": 2}, template=3),
    data=Switch(lambda this: this.type, requirement_type_map)
)
ConstructRequirementArray = Struct(
    comment=OptionalValue(String),
    items=PrefixedArray(VarInt, ConstructRequirement),
)

requirement_type_map["and"] = ConstructRequirementArray
requirement_type_map["or"] = ConstructRequirementArray

ConstructDockWeakness = Struct(
    index=VarInt,
    name=String,
    lock_type=VarInt,
    requirement=ConstructRequirement,
)

ConstructResourceDatabase = Struct(
    items=ConstructDict(ConstructItemResourceInfo),
    events=ConstructDict(ConstructResourceInfo),
    tricks=ConstructDict(ConstructTrickResourceInfo),
    damage=ConstructDict(ConstructResourceInfo),
    versions=ConstructDict(ConstructResourceInfo),
    misc=ConstructDict(ConstructResourceInfo),
    requirement_template=ConstructDict(ConstructRequirement),
    damage_reductions=PrefixedArray(VarInt, ConstructDamageReductions),
    energy_tank_item_index=String,
    item_percentage_index=OptionalValue(String),
    multiworld_magic_item_index=OptionalValue(String),
)

ConstructResourceGain = Struct(
    resource_type=ConstructResourceType,
    resource_name=String,
    amount=VarInt,
)

ConstructLoreType = construct.Enum(Byte, **{enum_value.value: i for i, enum_value in enumerate(LoreType)})

ConstructNodeCoordinates = Struct(
    x=Float64b,
    y=Float64b,
    z=Float64b,
)

NodeBaseFields = {
    "heal": Flag,
    "coordinates": OptionalValue(ConstructNodeCoordinates),
    "description": String,
    "extra": JsonEncodedValue,
    "connections": ConstructDict(ConstructRequirement),
}


class NodeAdapter(construct.Adapter):
    def _decode(self, obj: construct.Container, context, path):
        result = construct.Container(node_type=obj["node_type"])
        result.update(obj["data"])
        result.move_to_end("connections")
        return result

    def _encode(self, obj: construct.Container, context, path):
        data = copy.copy(obj)
        return construct.Container(
            node_type=data.pop("node_type"),
            data=data,
        )


ConstructNode = NodeAdapter(Struct(
    node_type=construct.Enum(Byte, generic=0, dock=1, pickup=2, teleporter=3, event=4, translator_gate=5,
                             logbook=6, player_ship=7),
    data=Switch(
        lambda this: this.node_type,
        {
            "generic": Struct(
                **NodeBaseFields,
            ),
            "dock": Struct(
                **NodeBaseFields,
                destination=ConstructNodeIdentifier,
                dock_type=Byte,
                dock_weakness_index=VarInt,
            ),
            "pickup": Struct(
                **NodeBaseFields,
                pickup_index=VarInt,
                major_location=Flag,
            ),
            "teleporter": Struct(
                **NodeBaseFields,
                destination=ConstructAreaIdentifier,
                keep_name_when_vanilla=Flag,
                editable=Flag,
            ),
            "event": Struct(
                **NodeBaseFields,
                event_name=String,
            ),
            "translator_gate": Struct(
                **NodeBaseFields,
                gate_index=VarInt,
            ),
            "logbook": Struct(
                **NodeBaseFields,
                string_asset_id=VarInt,
                lore_type=ConstructLoreType,
            ),
            "player_ship": Struct(
                **NodeBaseFields,
                is_unlocked=ConstructRequirement,
            )
        }
)))

ConstructArea = Struct(
    default_node=OptionalValue(String),
    valid_starting_location=Flag,
    extra=JsonEncodedValue,
    nodes=ConstructDict(ConstructNode),
)

ConstructWorld = Struct(
    name=String,
    extra=JsonEncodedValue,
    areas=ConstructDict(ConstructArea),
)

ConstructGameEnum = construct.Enum(Byte, **{enum_item.value: i for i, enum_item in enumerate(RandovaniaGame)})

ConstructMinimalLogicDatabase = Struct(
    items_to_exclude=PrefixedArray(VarInt, Struct(
        name=String,
        when_shuffled=OptionalValue(String),
    )),
    custom_item_amount=PrefixedArray(VarInt, Struct(
        name=String,
        value=VarInt,
    )),
    events_to_exclude=PrefixedArray(VarInt, Struct(
        name=String,
        reason=OptionalValue(String),
    )),
)

ConstructGame = Struct(
    magic_number=Const(b"Req."),
    format_version=Const(current_format_version, Int32ub),
    schema_version=Const(schema_migration.CURRENT_DATABASE_VERSION, VarInt),
    game=ConstructGameEnum,
    resource_database=ConstructResourceDatabase,
    dock_weakness_database=Struct(
        door=PrefixedArray(VarInt, ConstructDockWeakness),
        portal=PrefixedArray(VarInt, ConstructDockWeakness),
        morph_ball=PrefixedArray(VarInt, ConstructDockWeakness),
    ),
    minimal_logic=OptionalValue(ConstructMinimalLogicDatabase),
    victory_condition=ConstructRequirement,
    starting_location=ConstructAreaIdentifier,
    initial_states=ConstructDict(PrefixedArray(VarInt, ConstructResourceGain)),
    worlds=PrefixedArray(VarInt, ConstructWorld),
)
