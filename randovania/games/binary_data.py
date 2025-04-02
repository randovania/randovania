from __future__ import annotations

import copy
from typing import TYPE_CHECKING, BinaryIO

import construct
from construct import (
    Byte,
    Compressed,
    Const,
    Default,
    Flag,
    Float32b,
    Float64b,
    Int32ub,
    PrefixedArray,
    Short,
    Struct,
    Switch,
    VarInt,
)

from randovania.game.game_enum import RandovaniaGame
from randovania.game_description import game_migration
from randovania.game_description.db.hint_node import HintNodeKind
from randovania.lib.construct_lib import (
    ConstructDict,
    DefaultsAdapter,
    JsonEncodedValue,
    OptionalValue,
    String,
    convert_to_raw_python,
)

if TYPE_CHECKING:
    from pathlib import Path

current_format_version = 11

_EXPECTED_FIELDS = [
    "schema_version",
    "game",
    "resource_database",
    "layers",
    "starting_location",
    "minimal_logic",
    "victory_condition",
    "dock_weakness_database",
    "hint_feature_database",
    "used_trick_levels",
    "flatten_to_set_on_patch",
    "regions",
]


def decode(binary_io: BinaryIO) -> dict:
    decoded = ConstructGame.parse_stream(binary_io)
    result: dict = convert_to_raw_python(decoded["db"])

    if unknown_keys := [key for key in result if key not in _EXPECTED_FIELDS]:
        raise ValueError(f"Unexpected fields in decoded data: {unknown_keys}")

    return result


def decode_file_path(binary_file_path: Path) -> dict:
    with binary_file_path.open("rb") as binary_io:
        return decode(binary_io)


def encode(original_data: dict, x: BinaryIO) -> None:
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
    region=String,
    area=String,
)

ConstructNodeIdentifier = construct.Struct(
    region=String,
    area=String,
    node=String,
)

ConstructResourceInfo = _build_resource_info()

ConstructItemResourceInfo = _build_resource_info(
    max_capacity=Int32ub,
)

ConstructTrickResourceInfo = _build_resource_info(
    description=String,
    require_documentation_above=Byte,
)

ConstructDamageReductions = Struct(
    name=String,
    reductions=PrefixedArray(
        VarInt,
        Struct(
            name=String,
            multiplier=Float32b,
        ),
    ),
)

ConstructResourceType = construct.Enum(Byte, items=0, events=1, tricks=2, damage=3, versions=4, misc=5)

ConstructResourceRequirement = Struct(
    type=ConstructResourceType,
    name=String,
    amount=Short,
    negate=Flag,
)

requirement_type_map = {
    "resource": ConstructResourceRequirement,
    "template": String,
    "node": ConstructNodeIdentifier,
}

ConstructRequirement = Struct(
    type=construct.Enum(Byte, resource=0, **{"and": 1, "or": 2}, template=3, node=4),
    data=Switch(lambda this: this.type, requirement_type_map),
)
ConstructRequirementArray = Struct(
    comment=OptionalValue(String),
    items=PrefixedArray(VarInt, ConstructRequirement),
)

requirement_type_map["and"] = ConstructRequirementArray
requirement_type_map["or"] = ConstructRequirementArray

ConstructDockLock = Struct(
    lock_type=String,
    requirement=ConstructRequirement,
)

ConstructDockWeakness = Struct(
    extra=JsonEncodedValue,
    requirement=ConstructRequirement,
    lock=OptionalValue(ConstructDockLock),
)

ConstructNamedTemplate = Struct(
    display_name=String,
    requirement=ConstructRequirement,
)

ConstructResourceDatabase = Struct(
    items=ConstructDict(ConstructItemResourceInfo),
    events=ConstructDict(ConstructResourceInfo),
    tricks=ConstructDict(ConstructTrickResourceInfo),
    damage=ConstructDict(ConstructResourceInfo),
    versions=ConstructDict(ConstructResourceInfo),
    misc=ConstructDict(ConstructResourceInfo),
    requirement_template=ConstructDict(ConstructNamedTemplate),
    damage_reductions=PrefixedArray(VarInt, ConstructDamageReductions),
    energy_tank_item_index=String,
)

ConstructResourceGain = Struct(
    resource_type=ConstructResourceType,
    resource_name=String,
    amount=VarInt,
)

ConstructHintNodeKind = construct.Enum(Byte, **{enum_value.value: i for i, enum_value in enumerate(HintNodeKind)})

ConstructNodeCoordinates = Struct(
    x=Float64b,
    y=Float64b,
    z=Float64b,
)

NodeBaseFields = {
    "heal": Flag,
    "coordinates": OptionalValue(ConstructNodeCoordinates),
    "description": String,
    "layers": PrefixedArray(VarInt, String),
    "extra": JsonEncodedValue,
    "connections": ConstructDict(ConstructRequirement),
    "valid_starting_location": Flag,
}


class NodeAdapter(construct.Adapter):
    def _decode(self, obj: construct.Container, context, path):
        result = construct.Container(node_type=obj["node_type"])
        result.update(obj["data"])
        result["connections"] = result.pop("connections")
        return result

    def _encode(self, obj: construct.Container, context, path):
        data = copy.copy(obj)
        return construct.Container(
            node_type=data.pop("node_type"),
            data=data,
        )


ConstructNode = NodeAdapter(
    Struct(
        node_type=construct.Enum(
            Byte, generic=0, dock=1, pickup=2, event=4, configurable_node=5, hint=6, teleporter_network=7
        ),
        data=Switch(
            lambda this: this.node_type,
            {
                "generic": Struct(
                    **NodeBaseFields,
                ),
                "dock": Struct(
                    **NodeBaseFields,
                    dock_type=String,
                    default_connection=ConstructNodeIdentifier,
                    default_dock_weakness=String,
                    exclude_from_dock_rando=Flag,
                    incompatible_dock_weaknesses=PrefixedArray(VarInt, String),
                    override_default_open_requirement=OptionalValue(ConstructRequirement),
                    override_default_lock_requirement=OptionalValue(ConstructRequirement),
                    ui_custom_name=OptionalValue(String),
                ),
                "pickup": Struct(
                    **NodeBaseFields,
                    pickup_index=VarInt,
                    location_category=construct.Enum(Byte, major=0, minor=1),
                    custom_index_group=OptionalValue(String),
                    hint_features=PrefixedArray(VarInt, String),
                ),
                "event": Struct(
                    **NodeBaseFields,
                    event_name=String,
                ),
                "configurable_node": Struct(
                    **NodeBaseFields,
                ),
                "hint": Struct(
                    **NodeBaseFields,
                    kind=ConstructHintNodeKind,
                    requirement_to_collect=ConstructRequirement,
                ),
                "teleporter_network": Struct(
                    **NodeBaseFields,
                    is_unlocked=ConstructRequirement,
                    network=String,
                    requirement_to_activate=ConstructRequirement,
                ),
            },
        ),
    )
)

ConstructArea = Struct(
    default_node=OptionalValue(String),
    hint_features=PrefixedArray(VarInt, String),
    extra=JsonEncodedValue,
    nodes=ConstructDict(ConstructNode),
)

ConstructRegion = Struct(
    name=String,
    extra=JsonEncodedValue,
    areas=ConstructDict(ConstructArea),
)

ConstructGameEnum = construct.Enum(Byte, **{enum_item.value: i for i, enum_item in enumerate(RandovaniaGame)})

ConstructMinimalLogicDatabase = Struct(
    items_to_exclude=PrefixedArray(
        VarInt,
        Struct(
            name=String,
            when_shuffled=OptionalValue(String),
        ),
    ),
    custom_item_amount=PrefixedArray(
        VarInt,
        Struct(
            name=String,
            value=VarInt,
        ),
    ),
    events_to_exclude=PrefixedArray(
        VarInt,
        Struct(
            name=String,
            reason=OptionalValue(String),
        ),
    ),
    description=String,
)

ConstructDockWeaknessDatabase = Struct(
    types=ConstructDict(
        Struct(
            name=String,
            extra=JsonEncodedValue,
            items=ConstructDict(ConstructDockWeakness),
            dock_rando=OptionalValue(
                Struct(
                    unlocked=String,
                    locked=String,
                    change_from=PrefixedArray(VarInt, String),
                    change_to=PrefixedArray(VarInt, String),
                )
            ),
        )
    ),
    default_weakness=Struct(
        type=String,
        name=String,
    ),
    dock_rando=Struct(
        force_change_two_way=Flag,
        resolver_attempts=VarInt,
        to_shuffle_proportion=Float64b,
    ),
)

ConstructUsedTrickLevels = OptionalValue(ConstructDict(PrefixedArray(VarInt, construct.Byte)))

ConstructHintFeatureDatabase = ConstructDict(
    DefaultsAdapter(
        Struct(
            long_name=String,
            hint_details=String[2],
            hidden=Default(Flag, False),
            description=Default(String, ""),
        )
    )
)


ConstructGame = Struct(
    magic_number=Const(b"Req."),
    format_version=Const(current_format_version, Int32ub),
    db=Compressed(
        Struct(
            schema_version=Const(game_migration.CURRENT_VERSION, VarInt),
            game=ConstructGameEnum,
            resource_database=ConstructResourceDatabase,
            layers=PrefixedArray(VarInt, String),
            starting_location=ConstructNodeIdentifier,
            minimal_logic=OptionalValue(ConstructMinimalLogicDatabase),
            victory_condition=ConstructRequirement,
            dock_weakness_database=ConstructDockWeaknessDatabase,
            hint_feature_database=ConstructHintFeatureDatabase,
            used_trick_levels=ConstructUsedTrickLevels,
            flatten_to_set_on_patch=Flag,
            regions=PrefixedArray(VarInt, ConstructRegion),
        ),
        "lzma",
    ),
)
