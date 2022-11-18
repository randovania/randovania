import copy
import json
from pathlib import Path
from typing import Callable, TypeVar, Hashable, Any

from randovania.game_description import game_migration
from randovania.game_description.game_description import GameDescription, MinimalLogicData, IndexWithReason
from randovania.game_description.requirements.base import Requirement
from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.requirement_or import RequirementOr
from randovania.game_description.requirements.requirement_template import RequirementTemplate
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.damage_resource_info import DamageReduction
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import ResourceInfo, ResourceGainTuple
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.resources.search import (
    MissingResource, find_resource_info_with_id,
    find_resource_info_with_long_name
)
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo
from randovania.game_description.resources.trick_resource_info import TrickResourceInfo
from randovania.game_description.world import event_pickup
from randovania.game_description.world.area import Area
from randovania.game_description.world.area_identifier import AreaIdentifier
from randovania.game_description.world.configurable_node import ConfigurableNode
from randovania.game_description.world.dock import (
    DockRandoConfig, DockRandoParams, DockWeakness, DockType, DockWeaknessDatabase, DockLockType, DockLock
)
from randovania.game_description.world.dock_lock_node import DockLockNode
from randovania.game_description.world.dock_node import DockNode
from randovania.game_description.world.event_node import EventNode
from randovania.game_description.world.logbook_node import LoreType, LogbookNode
from randovania.game_description.world.node import (
    GenericNode, Node,
    NodeLocation
)
from randovania.game_description.world.node_identifier import NodeIdentifier
from randovania.game_description.world.pickup_node import PickupNode
from randovania.game_description.world.player_ship_node import PlayerShipNode
from randovania.game_description.world.teleporter_node import TeleporterNode
from randovania.game_description.world.world import World
from randovania.game_description.world.world_list import WorldList
from randovania.games.game import RandovaniaGame
from randovania.lib import frozen_lib

X = TypeVar('X')
Y = TypeVar('Y')


def read_dict(data: dict[str, Y], item_reader: Callable[[str, Y], X]) -> list[X]:
    return [item_reader(name, item) for name, item in data.items()]


def read_array(data: list[Y], item_reader: Callable[[Y], X]) -> list[X]:
    return [item_reader(item) for item in data]


#

class ResourceReader:
    def __init__(self, next_index: int = 0):
        self.next_index = next_index

    def make_index(self):
        result = self.next_index
        self.next_index += 1
        return result

    def read_resource_info(self, name: str, data: dict, resource_type: ResourceType) -> SimpleResourceInfo:
        return SimpleResourceInfo(self.make_index(), data["long_name"],
                                  name, resource_type, frozen_lib.wrap(data["extra"]))

    def read_item_resource_info(self, name: str, data: dict) -> ItemResourceInfo:
        return ItemResourceInfo(self.make_index(), data["long_name"],
                                name, data["max_capacity"], frozen_lib.wrap(data["extra"]))

    def read_trick_resource_info(self, name: str, data: dict) -> TrickResourceInfo:
        return TrickResourceInfo(self.make_index(), data["long_name"],
                                 name, data["description"], frozen_lib.wrap(data["extra"]))

    def read_resource_info_array(self, data: dict[str, dict], resource_type: ResourceType) -> list[SimpleResourceInfo]:
        return read_dict(data, lambda name, info: self.read_resource_info(name, info, resource_type=resource_type))


# Damage

def read_damage_reduction(data: dict, items: list[ItemResourceInfo]) -> DamageReduction:
    return DamageReduction(find_resource_info_with_id(items, data["name"], ResourceType.ITEM)
                           if data["name"] is not None else None,
                           data["multiplier"])


def read_damage_reductions(data: list[dict], items: list[ItemResourceInfo]) -> tuple[DamageReduction, ...]:
    return tuple(read_damage_reduction(info, items) for info in data)


def read_resource_reductions_dict(data: list[dict], db: ResourceDatabase,
                                  ) -> dict[SimpleResourceInfo, list[DamageReduction]]:
    return {
        db.get_by_type_and_index(ResourceType.DAMAGE, item["name"]): read_damage_reductions(item["reductions"],
                                                                                            db.item)
        for item in data
    }


# Requirement


def read_resource_requirement(data: dict, resource_database: ResourceDatabase
                              ) -> ResourceRequirement:
    data = data["data"]
    return ResourceRequirement.with_data(
        resource_database,
        ResourceType.from_str(data["type"]), data["name"],
        data["amount"], data["negate"])


def read_requirement_array(data: dict,
                           resource_database: ResourceDatabase,
                           cls: type[X],
                           ) -> X:
    # Old version
    if isinstance(data["data"], list):
        return cls(
            [
                read_requirement(item, resource_database)
                for item in data["data"]
            ],
            None
        )

    return cls(
        [
            read_requirement(item, resource_database)
            for item in data["data"]["items"]
        ],
        data["data"]["comment"],
    )


def read_requirement_template(data: dict, resource_database: ResourceDatabase) -> RequirementTemplate:
    return RequirementTemplate(data["data"])


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

    else:
        raise ValueError(f"Unknown requirement type: {req_type}")


def read_optional_requirement(data: dict | None, resource_database: ResourceDatabase) -> Requirement | None:
    if data is None:
        return None
    else:
        return read_requirement(data, resource_database)


# Resource Gain

def read_single_resource_gain(item: dict, database: "ResourceDatabase") -> tuple[ResourceInfo, int]:
    resource = database.get_by_type_and_index(ResourceType.from_str(item["resource_type"]),
                                              item["resource_name"])
    amount = item["amount"]

    return resource, amount


def read_resource_gain_tuple(data: list[dict], database: "ResourceDatabase") -> ResourceGainTuple:
    return tuple(
        read_single_resource_gain(item, database)
        for item in data
    )


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


def read_dock_weakness_database(data: dict,
                                resource_database: ResourceDatabase,
                                ) -> DockWeaknessDatabase:
    dock_types = read_dict(data["types"], read_dock_type)
    weaknesses: dict[DockType, dict[str, DockWeakness]] = {}
    dock_rando: dict[DockType, DockRandoParams] = {}
    next_index = 0

    def get_index():
        nonlocal next_index
        result = next_index
        next_index += 1
        return result

    for dock_type, type_data in zip(dock_types, data["types"].values()):
        weaknesses[dock_type] = {
            weak_name: read_dock_weakness(get_index(), weak_name, weak_data, resource_database)
            for weak_name, weak_data in type_data["items"].items()
        }

        def weakness_or_none(weak):
            return weak if weak is None else weaknesses[dock_type][weak]

        dr = type_data["dock_rando"]
        dock_rando[dock_type] = DockRandoParams(
            unlocked=weakness_or_none(dr["unlocked"]),
            locked=weakness_or_none(dr["locked"]),
            change_from={weaknesses[dock_type][weak] for weak in dr["change_from"]},
            change_to={weaknesses[dock_type][weak] for weak in dr["change_to"]},
        )

    default_dock_type = [dock_type for dock_type in dock_types
                         if dock_type.short_name == data["default_weakness"]["type"]][0]
    default_dock_weakness = weaknesses[default_dock_type][data["default_weakness"]["name"]]

    dock_rando_config = DockRandoConfig(
        enable_one_way=data["dock_rando"]["enable_one_way"],
        force_change_two_way=data["dock_rando"]["force_change_two_way"],
        resolver_attempts=data["dock_rando"]["resolver_attempts"],
        to_shuffle_proportion=data["dock_rando"]["to_shuffle_proportion"],
    )

    return DockWeaknessDatabase(
        dock_types=dock_types,
        weaknesses=weaknesses,
        dock_rando_params=dock_rando,
        default_weakness=(default_dock_type, default_dock_weakness),
        dock_rando_config=dock_rando_config
    )


def location_from_json(location: dict[str, float]) -> NodeLocation:
    return NodeLocation(float(location["x"]), float(location["y"]), float(location["z"]))


class WorldReader:
    resource_database: ResourceDatabase
    dock_weakness_database: DockWeaknessDatabase
    current_world_name: str
    current_area_name: str
    next_node_index: int

    def __init__(self,
                 resource_database: ResourceDatabase,
                 dock_weakness_database: DockWeaknessDatabase,
                 ):
        self.resource_database = resource_database
        self.dock_weakness_database = dock_weakness_database
        self.next_node_index = 0

    def _get_scan_visor(self) -> ItemResourceInfo:
        try:
            return find_resource_info_with_long_name(
                self.resource_database.item,
                "Scan Visor"
            )
        except MissingResource:
            return None

    def _get_command_visor(self) -> ItemResourceInfo:
        try:
            return find_resource_info_with_long_name(
                self.resource_database.item,
                "Command Visor"
            )
        except MissingResource:
            return None

    def read_node(self, name: str, data: dict) -> Node:
        try:
            location = None
            if data["coordinates"] is not None:
                location = location_from_json(data["coordinates"])

            generic_args = {
                "identifier": NodeIdentifier.create(self.current_world_name, self.current_area_name, name),
                "node_index": self.next_node_index,
                "heal": data["heal"],
                "location": location,
                "description": data["description"],
                "layers": tuple(data["layers"]),
                "extra": frozen_lib.wrap(data["extra"]),
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
                )

            elif node_type == "pickup":
                return PickupNode(
                    **generic_args,
                    pickup_index=PickupIndex(data["pickup_index"]),
                    major_location=data["major_location"],
                )

            elif node_type == "teleporter":
                return TeleporterNode(
                    **generic_args,
                    default_connection=AreaIdentifier.from_json(data["destination"]),
                    keep_name_when_vanilla=data["keep_name_when_vanilla"],
                    editable=data["editable"],
                )

            elif node_type == "event":
                return EventNode(
                    **generic_args,
                    event=self.resource_database.get_by_type_and_index(ResourceType.EVENT, data["event_name"])
                )

            elif node_type == "configurable_node":
                return ConfigurableNode(
                    **generic_args,
                )

            elif node_type == "logbook":
                lore_type = LoreType(data["lore_type"])

                if lore_type == LoreType.REQUIRES_ITEM:
                    required_translator = self.resource_database.get_item(data["extra"]["translator"])
                else:
                    required_translator = None

                if lore_type in {LoreType.SPECIFIC_PICKUP, LoreType.SKY_TEMPLE_KEY_HINT}:
                    hint_index = data["extra"]["hint_index"]
                else:
                    hint_index = None

                return LogbookNode(
                    **generic_args,
                    string_asset_id=data["string_asset_id"],
                    scan_visor=self._get_scan_visor(),
                    lore_type=lore_type,
                    required_translator=required_translator,
                    hint_index=hint_index,
                )

            elif node_type == "player_ship":
                return PlayerShipNode(
                    **generic_args,
                    is_unlocked=read_requirement(data["is_unlocked"], self.resource_database),
                    item_to_summon=self._get_command_visor(),
                )

            else:
                raise Exception(f"Unknown type: {node_type}")

        except Exception as e:
            raise Exception(f"In node {name}, got error: {e}")

    def read_area(self, area_name: str, data: dict) -> Area:
        self.current_area_name = area_name
        nodes = [self.read_node(node_name, item) for node_name, item in data["nodes"].items()]
        nodes_by_name = {node.name: node for node in nodes}

        connections = {}
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
                lock_node = DockLockNode.create_from_dock(node, self.next_node_index)
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
            return Area(area_name, data["default_node"],
                        data["valid_starting_location"],
                        nodes, connections, data["extra"])
        except KeyError as e:
            raise KeyError(f"Missing key `{e}` for area `{area_name}`")

    def read_area_list(self, data: dict[str, dict]) -> list[Area]:
        return [self.read_area(name, item) for name, item in data.items()]

    def read_world(self, data: dict) -> World:
        self.current_world_name = data["name"]
        return World(
            data["name"],
            self.read_area_list(data["areas"]),
            frozen_lib.wrap(data["extra"]),
        )

    def read_world_list(self, data: list[dict]) -> WorldList:
        return WorldList(read_array(data, self.read_world))


def read_requirement_templates(data: dict, database: ResourceDatabase) -> dict[str, Requirement]:
    return {
        name: read_requirement(item, database)
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
        energy_tank_item_index=data["energy_tank_item_index"],
        item_percentage_index=data["item_percentage_index"],
        multiworld_magic_item_index=data["multiworld_magic_item_index"]
    )
    db.requirement_template.update(read_requirement_templates(data["requirement_template"], db))
    db.damage_reductions.update(read_resource_reductions_dict(data["damage_reductions"], db))
    return db


def read_initial_states(data: dict[str, list], resource_database: ResourceDatabase) -> dict[str, ResourceGainTuple]:
    return {
        name: read_resource_gain_tuple(item, resource_database)
        for name, item in data.items()
    }


def read_minimal_logic_db(data: dict | None) -> MinimalLogicData | None:
    if data is None:
        return None

    return MinimalLogicData(
        items_to_exclude=[
            IndexWithReason(it["name"], it.get("when_shuffled"))
            for it in data["items_to_exclude"]
        ],
        custom_item_amount={
            it["name"]: it["value"]
            for it in data["custom_item_amount"]
        },
        events_to_exclude=[
            IndexWithReason(it["name"], it.get("reason"))
            for it in data["events_to_exclude"]
        ],
        description=data["description"]
    )


def decode_data_with_world_reader(data: dict) -> tuple[WorldReader, GameDescription]:
    data = game_migration.migrate_to_current(data)

    game = RandovaniaGame(data["game"])

    resource_database = read_resource_database(game, data["resource_database"])
    dock_weakness_database = read_dock_weakness_database(data["dock_weakness_database"], resource_database)

    layers = frozen_lib.wrap(data["layers"])
    world_reader = WorldReader(resource_database, dock_weakness_database)
    world_list = world_reader.read_world_list(data["worlds"])

    victory_condition = read_requirement(data["victory_condition"], resource_database)
    starting_location = AreaIdentifier.from_json(data["starting_location"])
    initial_states = read_initial_states(data["initial_states"], resource_database)
    minimal_logic = read_minimal_logic_db(data["minimal_logic"])

    return world_reader, GameDescription(
        game=game,
        resource_database=resource_database,
        layers=layers,
        dock_weakness_database=dock_weakness_database,
        world_list=world_list,
        victory_condition=victory_condition,
        starting_location=starting_location,
        initial_states=initial_states,
        minimal_logic=minimal_logic,
    )


def decode_data(data: dict) -> GameDescription:
    return decode_data_with_world_reader(data)[1]


def read_split_file(dir_path: Path):
    with dir_path.joinpath("header.json").open(encoding="utf-8") as meta_file:
        data = read_json_file(meta_file)

    worlds = data.pop("worlds")
    data["worlds"] = []
    for world_file_name in worlds:
        with dir_path.joinpath(world_file_name).open(encoding="utf-8") as world_file:
            data["worlds"].append(read_json_file(world_file))

    return data


def raise_on_duplicate_keys(ordered_pairs: list[tuple[Hashable, Any]]) -> dict:
    """Raise ValueError if a duplicate key exists in provided ordered list of pairs, otherwise return a dict."""
    dict_out = {}
    for key, val in ordered_pairs:
        if key in dict_out:
            raise ValueError(f'Duplicate key: {key}')
        else:
            dict_out[key] = val
    return dict_out


def read_json_file(file):
    """json.load, but rejects duplicated keys"""
    return json.load(file, object_pairs_hook=raise_on_duplicate_keys)
