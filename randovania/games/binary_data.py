import copy
from pathlib import Path
from typing import BinaryIO, Dict

import construct
from construct import (Struct, Int32ub, Const, Byte, Float32b, Flag,
                       Short, PrefixedArray, Switch, VarInt, Float64b, Compressed)

from randovania.game_description import game_migration
from randovania.game_description.world.node import LoreType
from randovania.games.game import RandovaniaGame
from randovania.lib.construct_lib import String, convert_to_raw_python, OptionalValue, ConstructDict, JsonEncodedValue

current_format_version = 10

_EXPECTED_FIELDS = [
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


def decode(binary_io: BinaryIO) -> dict:
    decoded = ConstructGame.parse_stream(binary_io)
    result: dict = convert_to_raw_python(decoded["db"])

    if unknown_keys := [key for key in result if key not in _EXPECTED_FIELDS]:
        raise ValueError(f"Unexpected fields in decoded data: {unknown_keys}")

    return result


def decode_file_path(binary_file_path: Path) -> Dict:
    with binary_file_path.open("rb") as binary_io:
        return decode(binary_io)


def encode(original_data: Dict, x: BinaryIO) -> None:
    if unknown_keys := [key for key in original_data if key not in _EXPECTED_FIELDS]:
        raise ValueError(f"Unexpected fields in data to be encoded: {unknown_keys}")

    data = copy.deepcopy(original_data)
    ConstructGame.build_stream({"db": data}, x)


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

ConstructResourceType = construct.Enum(Byte, items=0, events=1, tricks=2, damage=3, versions=4, misc=5, pickup_index=7,
                                       gate_index=8, logbook_index=9, ship_node=10)

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
    lock_type=VarInt,
    extra=JsonEncodedValue,
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
    node_type=construct.Enum(Byte, generic=0, dock=1, pickup=2, teleporter=3, event=4, configurable_node=5,
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
                dock_type=String,
                dock_weakness=String,
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
            "configurable_node": Struct(
                **NodeBaseFields,
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
    description=String,
)

ConstructDockWeaknessDatabase = Struct(
    types=ConstructDict(Struct(
        name=String,
        extra=JsonEncodedValue,
        items=ConstructDict(ConstructDockWeakness),
    )),
    default_weakness=Struct(
        type=String,
        name=String,
    )
)

ConstructGame = Struct(
    magic_number=Const(b"Req."),
    format_version=Const(current_format_version, Int32ub),
    db=Compressed(Struct(
        schema_version=Const(game_migration.CURRENT_VERSION, VarInt),
        game=ConstructGameEnum,
        resource_database=ConstructResourceDatabase,

        starting_location=ConstructAreaIdentifier,
        initial_states=ConstructDict(PrefixedArray(VarInt, ConstructResourceGain)),
        minimal_logic=OptionalValue(ConstructMinimalLogicDatabase),
        victory_condition=ConstructRequirement,

        dock_weakness_database=ConstructDockWeaknessDatabase,
        worlds=PrefixedArray(VarInt, ConstructWorld),
    ), "lzma")
)
