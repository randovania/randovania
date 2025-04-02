from __future__ import annotations

import copy
import typing
from typing import TYPE_CHECKING, TypeVar

from randovania.game.game_enum import RandovaniaGame
from randovania.game_description import game_migration
from randovania.game_description.db import event_pickup
from randovania.game_description.db.area import Area
from randovania.game_description.db.configurable_node import ConfigurableNode
from randovania.game_description.db.dock import (
    DockLock,
    DockLockType,
    DockRandoConfig,
    DockRandoParams,
    DockType,
    DockWeakness,
    DockWeaknessDatabase,
)
from randovania.game_description.db.dock_lock_node import DockLockNode
from randovania.game_description.db.dock_node import DockNode
from randovania.game_description.db.event_node import EventNode
from randovania.game_description.db.hint_node import HintNode, HintNodeKind
from randovania.game_description.db.node import GenericNode, Node, NodeLocation
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.db.pickup_node import PickupNode
from randovania.game_description.db.region import Region
from randovania.game_description.db.region_list import RegionList
from randovania.game_description.db.teleporter_network_node import TeleporterNetworkNode
from randovania.game_description.game_description import GameDescription, IndexWithReason, MinimalLogicData
from randovania.game_description.hint_features import HintFeature
from randovania.game_description.requirements.node_requirement import NodeRequirement
from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.requirement_or import RequirementOr
from randovania.game_description.requirements.requirement_template import RequirementTemplate
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources import search
from randovania.game_description.resources.damage_reduction import DamageReduction
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.location_category import LocationCategory
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_database import NamedRequirementTemplate, ResourceDatabase
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.resources.search import MissingResource, find_resource_info_with_id
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo
from randovania.game_description.resources.trick_resource_info import TrickResourceInfo
from randovania.lib import frozen_lib, json_lib

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from randovania.game_description.requirements.array_base import RequirementArrayBase
    from randovania.game_description.requirements.base import Requirement
    from randovania.game_description.resources.resource_info import ResourceGainTuple, ResourceInfo

X = TypeVar("X")
Y = TypeVar("Y")


def read_dict(data: dict[str, Y], item_reader: Callable[[str, Y], X]) -> list[X]:
    return [item_reader(name, item) for name, item in data.items()]


def read_array(data: list[Y], item_reader: Callable[[Y], X]) -> list[X]:
    return [item_reader(item) for item in data]


#


class ResourceReader:
    def __init__(self, next_index: int = 0):
        self.next_index = next_index

    def make_index(self) -> int:
        result = self.next_index
        self.next_index += 1
        return result

    def read_resource_info(self, name: str, data: dict, resource_type: ResourceType) -> SimpleResourceInfo:
        return SimpleResourceInfo(
            self.make_index(), data["long_name"], name, resource_type, frozen_lib.wrap(data["extra"])
        )

    def read_item_resource_info(self, name: str, data: dict) -> ItemResourceInfo:
        return ItemResourceInfo(
            self.make_index(), data["long_name"], name, data["max_capacity"], frozen_lib.wrap(data["extra"])
        )

    def read_trick_resource_info(self, name: str, data: dict) -> TrickResourceInfo:
        return TrickResourceInfo(
            self.make_index(),
            data["long_name"],
            name,
            data["description"],
            data["require_documentation_above"],
            frozen_lib.wrap(data["extra"]),
        )

    def read_resource_info_array(self, data: dict[str, dict], resource_type: ResourceType) -> list[SimpleResourceInfo]:
        return read_dict(data, lambda name, info: self.read_resource_info(name, info, resource_type=resource_type))


# Damage


def read_damage_reduction(data: dict, items: list[ItemResourceInfo]) -> DamageReduction:
    return DamageReduction(
        find_resource_info_with_id(items, data["name"], ResourceType.ITEM) if data["name"] is not None else None,
        data["multiplier"],
    )


def read_damage_reductions(data: list[dict], items: list[ItemResourceInfo]) -> tuple[DamageReduction, ...]:
    return tuple(read_damage_reduction(info, items) for info in data)


def read_resource_reductions_dict(
    data: list[dict],
    db: ResourceDatabase,
) -> dict[SimpleResourceInfo, list[DamageReduction]]:
    return {db.get_damage(item["name"]): list(read_damage_reductions(item["reductions"], db.item)) for item in data}


# Requirement


def read_resource_requirement(data: dict, resource_database: ResourceDatabase) -> ResourceRequirement:
    data = data["data"]
    return ResourceRequirement.with_data(
        resource_database, ResourceType.from_str(data["type"]), data["name"], data["amount"], data["negate"]
    )


def read_requirement_array(
    data: dict,
    resource_database: ResourceDatabase,
    cls: type[RequirementArrayBase],
) -> RequirementArrayBase:
    # Old version
    if isinstance(data["data"], list):
        return cls([read_requirement(item, resource_database) for item in data["data"]], None)

    return cls(
        [read_requirement(item, resource_database) for item in data["data"]["items"]],
        data["data"]["comment"],
    )


def read_requirement_template(data: dict, resource_database: ResourceDatabase) -> RequirementTemplate:
    return RequirementTemplate(data["data"])


def read_node_requirement(data: dict, resource_database: ResourceDatabase) -> NodeRequirement:
    return NodeRequirement(NodeIdentifier.from_json(data["data"]))


def read_requirement(data: dict, resource_database: ResourceDatabase) -> Requirement:
    req_type = data["type"]
    if req_type == "resource":
        return read_resource_requirement(data, resource_database)

    elif req_type == "and":
        return read_requirement_array(data, resource_database, RequirementAnd)

    elif req_type == "or":
        return read_requirement_array(data, resource_database, RequirementOr)

    elif req_type == "template":
        return read_requirement_template(data, resource_database)

    elif req_type == "node":
        return read_node_requirement(data, resource_database)

    else:
        raise ValueError(f"Unknown requirement type: {req_type}")


def read_optional_requirement(data: dict | None, resource_database: ResourceDatabase) -> Requirement | None:
    if data is None:
        return None
    else:
        return read_requirement(data, resource_database)


# Resource Gain


def read_single_resource_gain(item: dict, database: ResourceDatabase) -> tuple[ResourceInfo, int]:
    resource = database.get_by_type_and_index(ResourceType.from_str(item["resource_type"]), item["resource_name"])
    amount = item["amount"]

    return resource, amount


def read_resource_gain_tuple(data: list[dict], database: ResourceDatabase) -> ResourceGainTuple:
    return tuple(read_single_resource_gain(item, database) for item in data)


def read_dock_lock(data: dict | None, resource_database: ResourceDatabase) -> DockLock | None:
    if data is None:
        return None
    return DockLock(
        lock_type=DockLockType(data["lock_type"]),
        requirement=read_requirement(data["requirement"], resource_database),
    )


# Dock Weakness


def read_dock_weakness(index: int, name: str, item: dict, resource_database: ResourceDatabase) -> DockWeakness:
    return DockWeakness(
        index,
        name,
        frozen_lib.wrap(item["extra"]),
        read_requirement(item["requirement"], resource_database),
        read_dock_lock(item["lock"], resource_database),
    )


def read_dock_type(name: str, data: dict) -> DockType:
    return DockType(
        short_name=name,
        long_name=data["name"],
        extra=frozen_lib.wrap(data["extra"]),
    )


def read_dock_weakness_database(
    data: dict,
    resource_database: ResourceDatabase,
) -> DockWeaknessDatabase:
    dock_types = read_dict(data["types"], read_dock_type)
    weaknesses: dict[DockType, dict[str, DockWeakness]] = {}
    dock_rando: dict[DockType, DockRandoParams] = {}
    next_index = 0

    def get_index() -> int:
        nonlocal next_index
        result = next_index
        next_index += 1
        return result

    for dock_type, type_data in zip(dock_types, data["types"].values()):
        weaknesses[dock_type] = {
            weak_name: read_dock_weakness(get_index(), weak_name, weak_data, resource_database)
            for weak_name, weak_data in type_data["items"].items()
        }

        dr = type_data["dock_rando"]
        if dr is not None:
            dock_rando[dock_type] = DockRandoParams(
                unlocked=weaknesses[dock_type][dr["unlocked"]],
                locked=weaknesses[dock_type][dr["locked"]],
                change_from={weaknesses[dock_type][weak] for weak in dr["change_from"]},
                change_to={weaknesses[dock_type][weak] for weak in dr["change_to"]},
            )

    default_dock_type = [
        dock_type for dock_type in dock_types if dock_type.short_name == data["default_weakness"]["type"]
    ][0]
    default_dock_weakness = weaknesses[default_dock_type][data["default_weakness"]["name"]]

    dock_rando_config = DockRandoConfig(
        force_change_two_way=data["dock_rando"]["force_change_two_way"],
        resolver_attempts=data["dock_rando"]["resolver_attempts"],
        to_shuffle_proportion=data["dock_rando"]["to_shuffle_proportion"],
    )

    return DockWeaknessDatabase(
        dock_types=dock_types,
        weaknesses=weaknesses,
        dock_rando_params=dock_rando,
        default_weakness=(default_dock_type, default_dock_weakness),
        dock_rando_config=dock_rando_config,
    )


def location_from_json(location: dict[str, float]) -> NodeLocation:
    return NodeLocation(float(location["x"]), float(location["y"]), float(location["z"]))


# Hint Features
def read_hint_feature_database(data: dict[str, dict]) -> dict[str, HintFeature]:
    return {name: HintFeature.from_json(feature, name=name) for name, feature in data.items()}


class RegionReader:
    resource_database: ResourceDatabase
    dock_weakness_database: DockWeaknessDatabase
    hint_feature_database: dict[str, HintFeature]
    current_region_name: str
    current_area_name: str
    next_node_index: int

    def __init__(
        self,
        resource_database: ResourceDatabase,
        dock_weakness_database: DockWeaknessDatabase,
        hint_feature_database: dict[str, HintFeature],
    ):
        self.resource_database = resource_database
        self.dock_weakness_database = dock_weakness_database
        self.hint_feature_database = hint_feature_database
        self.next_node_index = 0

    def _get_item(self, item_name: str | None) -> ItemResourceInfo | None:
        if item_name is None:
            return None
        return self.resource_database.get_item(item_name)

    def read_node(self, name: str, data: dict) -> Node:
        try:
            location = None
            if data["coordinates"] is not None:
                location = location_from_json(data["coordinates"])

            generic_args = {
                "identifier": NodeIdentifier.create(self.current_region_name, self.current_area_name, name),
                "node_index": self.next_node_index,
                "heal": data["heal"],
                "location": location,
                "description": data["description"],
                "layers": tuple(data["layers"]),
                "extra": frozen_lib.wrap(data["extra"]),
                "valid_starting_location": data["valid_starting_location"],
            }
            self.next_node_index += 1
            node_type: int = data["node_type"]

            if node_type == "generic":
                return GenericNode(**generic_args)

            elif node_type == "dock":
                return DockNode(
                    **generic_args,
                    dock_type=self.dock_weakness_database.find_type(data["dock_type"]),
                    default_connection=NodeIdentifier.from_json(data["default_connection"]),
                    default_dock_weakness=self.dock_weakness_database.get_by_weakness(
                        data["dock_type"],
                        data["default_dock_weakness"],
                    ),
                    override_default_open_requirement=read_optional_requirement(
                        data["override_default_open_requirement"], self.resource_database
                    ),
                    override_default_lock_requirement=read_optional_requirement(
                        data["override_default_lock_requirement"], self.resource_database
                    ),
                    exclude_from_dock_rando=data["exclude_from_dock_rando"],
                    incompatible_dock_weaknesses=tuple(
                        [
                            self.dock_weakness_database.get_by_weakness(data["dock_type"], name)
                            for name in data["incompatible_dock_weaknesses"]
                        ]
                    ),
                    ui_custom_name=data["ui_custom_name"],
                )

            elif node_type == "pickup":
                return PickupNode(
                    **generic_args,
                    pickup_index=PickupIndex(data["pickup_index"]),
                    location_category=LocationCategory(data["location_category"]),
                    custom_index_group=data["custom_index_group"],
                    hint_features=frozenset(self.hint_feature_database[feature] for feature in data["hint_features"]),
                )

            elif node_type == "event":
                return EventNode(**generic_args, event=self.resource_database.get_event(data["event_name"]))

            elif node_type == "configurable_node":
                return ConfigurableNode(
                    **generic_args,
                )

            elif node_type == "hint":
                lock_requirement = read_requirement(data["requirement_to_collect"], self.resource_database)

                return HintNode(
                    **generic_args,
                    kind=HintNodeKind(data["kind"]),
                    lock_requirement=lock_requirement,
                )

            elif node_type == "teleporter_network":
                return TeleporterNetworkNode(
                    **generic_args,
                    is_unlocked=read_requirement(data["is_unlocked"], self.resource_database),
                    network=data["network"],
                    requirement_to_activate=read_requirement(data["requirement_to_activate"], self.resource_database),
                )

            else:
                raise Exception(f"Unknown type: {node_type}")

        except Exception as e:
            raise Exception(f"In node {name}, got error: {e}")

    def read_area(self, area_name: str, data: dict) -> Area:
        self.current_area_name = area_name
        nodes = [self.read_node(node_name, item) for node_name, item in data["nodes"].items()]
        nodes_by_name = {node.name: node for node in nodes}

        connections: dict[Node, dict[Node, Requirement]] = {}
        for origin in nodes:
            origin_data = data["nodes"][origin.name]
            try:
                connections[origin] = {}
            except TypeError as e:
                print(origin.extra)
                raise KeyError(f"Area {area_name}, node {origin}: {e}")

            for target_name, target_requirement in origin_data["connections"].items():
                try:
                    the_set = read_requirement(target_requirement, self.resource_database)
                    connections[origin][nodes_by_name[target_name]] = the_set
                except (MissingResource, KeyError) as e:
                    raise type(e)(f"In area {area_name}, connection from {origin.name} to {target_name} got error: {e}")

        for node in list(nodes):
            if isinstance(node, DockNode):
                lock_node = DockLockNode.create_from_dock(node, self.next_node_index, self.resource_database)
                nodes.append(lock_node)
                connections[lock_node] = {}
                self.next_node_index += 1

        for combo in event_pickup.find_nodes_to_combine(nodes, connections):
            combo_node = event_pickup.EventPickupNode.create_from(self.next_node_index, *combo)
            nodes.append(combo_node)
            for existing_connections in connections.values():
                if combo[0] in existing_connections:
                    existing_connections[combo_node] = copy.copy(existing_connections[combo[0]])
            connections[combo_node] = copy.copy(connections[combo[1]])
            self.next_node_index += 1

        try:
            return Area(
                name=area_name,
                nodes=nodes,
                connections=connections,
                extra=data["extra"],
                default_node=data["default_node"],
                hint_features=frozenset(self.hint_feature_database[feature] for feature in data["hint_features"]),
            )
        except KeyError as e:
            raise KeyError(f"Missing key `{e}` for area `{area_name}`")

    def read_area_list(self, data: dict[str, dict]) -> list[Area]:
        return [self.read_area(name, item) for name, item in data.items()]

    def read_region(self, data: dict) -> Region:
        self.current_region_name = data["name"]
        return Region(
            data["name"],
            self.read_area_list(data["areas"]),
            frozen_lib.wrap(data["extra"]),
        )

    def read_region_list(self, data: list[dict], flatten_to_set_on_patch: bool) -> RegionList:
        return RegionList(read_array(data, self.read_region), flatten_to_set_on_patch)


def read_requirement_templates(data: dict, database: ResourceDatabase) -> dict[str, NamedRequirementTemplate]:
    return {
        name: NamedRequirementTemplate(
            display_name=item["display_name"],
            requirement=read_requirement(item["requirement"], database),
        )
        for name, item in data.items()
    }


def read_resource_database(game: RandovaniaGame, data: dict) -> ResourceDatabase:
    reader = ResourceReader()

    item = read_dict(data["items"], reader.read_item_resource_info)

    db = ResourceDatabase(
        game_enum=game,
        item=item,
        event=reader.read_resource_info_array(data["events"], ResourceType.EVENT),
        trick=read_dict(data["tricks"], reader.read_trick_resource_info),
        damage=reader.read_resource_info_array(data["damage"], ResourceType.DAMAGE),
        version=reader.read_resource_info_array(data["versions"], ResourceType.VERSION),
        misc=reader.read_resource_info_array(data["misc"], ResourceType.MISC),
        requirement_template={},
        damage_reductions={},
        energy_tank_item=search.find_resource_info_with_id(item, data["energy_tank_item_index"], ResourceType.ITEM),
    )
    db.requirement_template.update(read_requirement_templates(data["requirement_template"], db))
    db.damage_reductions.update(read_resource_reductions_dict(data["damage_reductions"], db))
    return db


def read_minimal_logic_db(data: dict | None) -> MinimalLogicData | None:
    if data is None:
        return None

    return MinimalLogicData(
        items_to_exclude=[IndexWithReason(it["name"], it.get("when_shuffled")) for it in data["items_to_exclude"]],
        custom_item_amount={it["name"]: it["value"] for it in data["custom_item_amount"]},
        events_to_exclude=[IndexWithReason(it["name"], it.get("reason")) for it in data["events_to_exclude"]],
        description=data["description"],
    )


def read_used_trick_levels(
    data: dict[str, list[int]] | None, resource_database: ResourceDatabase
) -> dict[TrickResourceInfo, set[int]] | None:
    if data is None:
        return None
    return {resource_database.get_trick(trick): set(levels) for trick, levels in data.items()}


def decode_data_with_region_reader(data: dict) -> tuple[RegionReader, GameDescription]:
    game = RandovaniaGame(data["game"])
    data = game_migration.migrate_to_current(data, game)

    resource_database = read_resource_database(game, data["resource_database"])
    dock_weakness_database = read_dock_weakness_database(data["dock_weakness_database"], resource_database)
    hint_feature_database = read_hint_feature_database(data["hint_feature_database"])

    layers = frozen_lib.wrap(data["layers"])
    region_reader = RegionReader(resource_database, dock_weakness_database, hint_feature_database)
    region_list = region_reader.read_region_list(data["regions"], data["flatten_to_set_on_patch"])

    victory_condition = read_requirement(data["victory_condition"], resource_database)
    starting_location = NodeIdentifier.from_json(data["starting_location"])
    minimal_logic = read_minimal_logic_db(data["minimal_logic"])
    used_trick_levels = read_used_trick_levels(data["used_trick_levels"], resource_database)

    return region_reader, GameDescription(
        game=game,
        resource_database=resource_database,
        layers=layers,
        dock_weakness_database=dock_weakness_database,
        hint_feature_database=hint_feature_database,
        region_list=region_list,
        victory_condition=victory_condition,
        starting_location=starting_location,
        minimal_logic=minimal_logic,
        used_trick_levels=used_trick_levels,
    )


def decode_data(data: dict) -> GameDescription:
    return decode_data_with_region_reader(data)[1]


def read_split_file(dir_path: Path) -> dict:
    data = json_lib.read_path(dir_path.joinpath("header.json"), raise_on_duplicate_keys=True)
    assert isinstance(data, dict)

    key_name = "regions"
    if key_name not in data:
        # This code runs before we can run old data migration, so we need to handle this difference here
        key_name = "worlds"

    regions = typing.cast("list[str]", data.pop(key_name))

    data[key_name] = [
        json_lib.read_path(dir_path.joinpath(region_file_name), raise_on_duplicate_keys=True)
        for region_file_name in regions
    ]

    return data
