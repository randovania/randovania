import json
from pathlib import Path
from typing import List, Callable, TypeVar, Tuple, Dict, Type, Optional

from randovania.game_description.game_description import GameDescription, MinimalLogicData, IndexWithReason
from randovania.game_description.requirements import ResourceRequirement, Requirement, \
    RequirementOr, RequirementAnd, RequirementTemplate
from randovania.game_description.resources.damage_resource_info import DamageReduction
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import ResourceInfo, ResourceGainTuple
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.resources.search import MissingResource, find_resource_info_with_id, \
    find_resource_info_with_long_name
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo
from randovania.game_description.resources.translator_gate import TranslatorGate
from randovania.game_description.resources.trick_resource_info import TrickResourceInfo
from randovania.game_description.world.area import Area
from randovania.game_description.world.area_location import AreaLocation
from randovania.game_description.world.dock import DockWeakness, DockType, DockWeaknessDatabase, DockConnection, \
    DockLockType
from randovania.game_description.world.node import GenericNode, DockNode, TeleporterNode, PickupNode, EventNode, Node, \
    TranslatorGateNode, LogbookNode, LoreType, NodeLocation, PlayerShipNode
from randovania.game_description.world.teleporter import Teleporter
from randovania.game_description.world.world import World
from randovania.game_description.world.world_list import WorldList
from randovania.games.game import RandovaniaGame

X = TypeVar('X')
Y = TypeVar('Y')


def read_array(data: List[Y], item_reader: Callable[[Y], X]) -> List[X]:
    return [item_reader(item) for item in data]


def read_resource_info(data: Dict, resource_type: ResourceType) -> SimpleResourceInfo:
    return SimpleResourceInfo(data["index"], data["long_name"],
                              data["short_name"], resource_type)


def read_item_resource_info(data: Dict) -> ItemResourceInfo:
    return ItemResourceInfo(data["index"], data["long_name"],
                            data["short_name"], data["max_capacity"], data.get("extra"))


def read_trick_resource_info(data: Dict) -> TrickResourceInfo:
    return TrickResourceInfo(data["index"], data["long_name"],
                             data["short_name"], data["description"])


def read_resource_info_array(data: List[Dict], resource_type: ResourceType) -> List[SimpleResourceInfo]:
    return read_array(data, lambda info: read_resource_info(info, resource_type=resource_type))


# Damage

def read_damage_reduction(data: Dict, items: List[ItemResourceInfo]) -> DamageReduction:
    return DamageReduction(find_resource_info_with_id(items, data["index"], ResourceType.ITEM)
                           if data["index"] is not None else None,
                           data["multiplier"])


def read_damage_reductions(data: List[Dict], items: List[ItemResourceInfo]) -> Tuple[DamageReduction, ...]:
    return tuple(read_damage_reduction(info, items) for info in data)


def read_resource_reductions_dict(data: List[Dict], db: ResourceDatabase,
                                  ) -> Dict[SimpleResourceInfo, List[DamageReduction]]:
    return {
        db.get_by_type_and_index(ResourceType.DAMAGE, item["index"]): read_damage_reductions(item["reductions"],
                                                                                             db.item)
        for item in data
    }


# Requirement


def read_resource_requirement(data: Dict, resource_database: ResourceDatabase
                              ) -> ResourceRequirement:
    data = data["data"]
    return ResourceRequirement.with_data(
        resource_database,
        ResourceType(data["type"]), data["index"],
        data["amount"], data["negate"])


def read_requirement_array(data: Dict,
                           resource_database: ResourceDatabase,
                           cls: Type[X],
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


def read_requirement_template(data: Dict, resource_database: ResourceDatabase) -> RequirementTemplate:
    return RequirementTemplate(data["data"])


def read_requirement(data: Dict, resource_database: ResourceDatabase) -> Requirement:
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


# Resource Gain

def read_single_resource_gain(item: Dict, database: "ResourceDatabase") -> Tuple[ResourceInfo, int]:
    resource = database.get_by_type_and_index(ResourceType(item["resource_type"]),
                                              item["resource_index"])
    amount = item["amount"]

    return resource, amount


def read_resource_gain_tuple(data: List[Dict], database: "ResourceDatabase") -> ResourceGainTuple:
    return tuple(
        read_single_resource_gain(item, database)
        for item in data
    )


# Dock Weakness

def read_dock_weakness(item: Dict, resource_database: ResourceDatabase, dock_type: DockType) -> DockWeakness:
    return DockWeakness(item["index"],
                        item["name"],
                        DockLockType(item["lock_type"]),
                        read_requirement(item["requirement"], resource_database),
                        dock_type)


def read_dock_weakness_database(data: Dict,
                                resource_database: ResourceDatabase,
                                ) -> DockWeaknessDatabase:
    door_types = read_array(data["door"], lambda item: read_dock_weakness(item, resource_database, DockType.DOOR))
    portal_types = read_array(data["portal"], lambda item: read_dock_weakness(item, resource_database, DockType.PORTAL))
    morph_ball_types = read_array(data["morph_ball"], lambda item: read_dock_weakness(item, resource_database,
                                                                                      DockType.MORPH_BALL_DOOR))

    return DockWeaknessDatabase(
        door=door_types,
        morph_ball=morph_ball_types,
        other=[
            DockWeakness(0, "Other Door", DockLockType.FRONT_ALWAYS_BACK_FREE, Requirement.trivial(),
                         DockType.OTHER)
        ],
        portal=portal_types)


def location_from_json(location: Dict[str, float]) -> NodeLocation:
    return NodeLocation(location["x"], location["y"], location["z"])


class WorldReader:
    resource_database: ResourceDatabase
    dock_weakness_database: DockWeaknessDatabase
    generic_index: int = -1
    current_world: int
    current_area: int

    def __init__(self,
                 resource_database: ResourceDatabase,
                 dock_weakness_database: DockWeaknessDatabase,
                 ):

        self.resource_database = resource_database
        self.dock_weakness_database = dock_weakness_database

    def _get_scan_visor(self) -> ItemResourceInfo:
        return find_resource_info_with_long_name(
            self.resource_database.item,
            "Scan Visor"
        )

    def _get_command_visor(self) -> ItemResourceInfo:
        return find_resource_info_with_long_name(
            self.resource_database.item,
            "Command Visor"
        )

    def read_node(self, data: Dict) -> Node:
        name: str = data["name"]
        self.generic_index += 1
        try:
            heal: bool = data["heal"]
            node_type: int = data["node_type"]
            location = None
            if data["coordinates"] is not None:
                location = location_from_json(data["coordinates"])

            if node_type == "generic":
                return GenericNode(name, heal, location, self.generic_index)

            elif node_type == "dock":
                return DockNode(name, heal, location, self.generic_index, data["dock_index"],
                                DockConnection(data["connected_area_asset_id"], data["connected_dock_index"]),
                                self.dock_weakness_database.get_by_type_and_index(DockType(data["dock_type"]),
                                                                                  data["dock_weakness_index"]))

            elif node_type == "pickup":
                return PickupNode(name, heal, location, self.generic_index, PickupIndex(data["pickup_index"]),
                                  data["major_location"])

            elif node_type == "teleporter":
                instance_id = data["teleporter_instance_id"]

                destination_world_asset_id = data["destination_world_asset_id"]
                destination_area_asset_id = data["destination_area_asset_id"]

                return TeleporterNode(name, heal, location, self.generic_index,
                                      Teleporter(self.current_world, self.current_area, instance_id),
                                      AreaLocation(destination_world_asset_id, destination_area_asset_id),
                                      data["scan_asset_id"],
                                      data["keep_name_when_vanilla"],
                                      data["editable"],
                                      )

            elif node_type == "event":
                return EventNode(name, heal, location, self.generic_index,
                                 self.resource_database.get_by_type_and_index(ResourceType.EVENT, data["event_index"]))

            elif node_type == "translator_gate":
                return TranslatorGateNode(name, heal, location, self.generic_index,
                                          TranslatorGate(data["gate_index"]),
                                          self._get_scan_visor())

            elif node_type == "logbook":
                lore_type = LoreType(data["lore_type"])

                if lore_type == LoreType.LUMINOTH_LORE:
                    required_translator = self.resource_database.get_item(data["extra"])
                else:
                    required_translator = None

                if lore_type in {LoreType.LUMINOTH_WARRIOR, LoreType.SKY_TEMPLE_KEY_HINT}:
                    hint_index = data["extra"]
                else:
                    hint_index = None

                return LogbookNode(name, heal, location, self.generic_index, data["string_asset_id"],
                                   self._get_scan_visor(),
                                   lore_type,
                                   required_translator,
                                   hint_index)

            elif node_type == "player_ship":
                return PlayerShipNode(name, heal, location, self.generic_index,
                                      read_requirement(data["is_unlocked"], self.resource_database),
                                      self._get_command_visor())

            else:
                raise Exception(f"Unknown type: {node_type}")

        except Exception as e:
            raise Exception(f"In node {name}, got error: {e}")

    def read_area(self, data: Dict) -> Area:
        self.current_area = data["asset_id"]
        nodes = read_array(data["nodes"], self.read_node)
        nodes_by_name = {node.name: node for node in nodes}

        connections = {}
        for i, origin_data in enumerate(data["nodes"]):
            origin = nodes[i]
            connections[origin] = {}

            for target_name, target_requirement in origin_data["connections"].items():
                try:
                    the_set = read_requirement(target_requirement, self.resource_database)
                except MissingResource as e:
                    raise MissingResource(
                        f"In area {data['name']}, connection from {origin.name} to {target_name} got error: {e}")

                if the_set != Requirement.impossible():
                    connections[origin][nodes_by_name[target_name]] = the_set

        area_name = data["name"]
        try:
            return Area(area_name, data["in_dark_aether"], data["asset_id"], data["default_node_index"],
                        data["valid_starting_location"],
                        nodes, connections)
        except KeyError as e:
            raise KeyError(f"Missing key `{e}` for area `{area_name}`")

    def read_area_list(self, data: List[Dict]) -> List[Area]:
        return read_array(data, self.read_area)

    def read_world(self, data: Dict) -> World:
        self.current_world = data["asset_id"]
        return World(data["name"], data["dark_name"], data["asset_id"],
                     self.read_area_list(data["areas"]))

    def read_world_list(self, data: List[Dict]) -> WorldList:
        return WorldList(read_array(data, self.read_world))


def read_requirement_templates(data: Dict, database: ResourceDatabase) -> Dict[str, Requirement]:
    return {
        name: read_requirement(item, database)
        for name, item in data.items()
    }


def read_resource_database(game: RandovaniaGame, data: Dict) -> ResourceDatabase:
    item = read_array(data["items"], read_item_resource_info)
    db = ResourceDatabase(
        game_enum=game,
        item=item,
        event=read_resource_info_array(data["events"], ResourceType.EVENT),
        trick=read_array(data["tricks"], read_trick_resource_info),
        damage=read_resource_info_array(data["damage"], ResourceType.DAMAGE),
        version=read_resource_info_array(data["versions"], ResourceType.VERSION),
        misc=read_resource_info_array(data["misc"], ResourceType.MISC),
        requirement_template={},
        damage_reductions={},
        energy_tank_item_index=data["energy_tank_item_index"],
        item_percentage_index=data["item_percentage_index"],
        multiworld_magic_item_index=data["multiworld_magic_item_index"]
    )
    db.requirement_template.update(read_requirement_templates(data["requirement_template"], db))
    db.damage_reductions.update(read_resource_reductions_dict(data["damage_reductions"], db))
    return db


def read_initial_states(data: Dict[str, List], resource_database: ResourceDatabase) -> Dict[str, ResourceGainTuple]:
    return {
        name: read_resource_gain_tuple(item, resource_database)
        for name, item in data.items()
    }


def read_minimal_logic_db(data: Optional[dict]) -> Optional[MinimalLogicData]:
    if data is None:
        return None

    return MinimalLogicData(
        items_to_exclude=[
            IndexWithReason(it["index"], it.get("when_shuffled"))
            for it in data["items_to_exclude"]
        ],
        custom_item_amount={
            it["index"]: it["value"]
            for it in data["custom_item_amount"]
        },
        events_to_exclude=[
            IndexWithReason(it["index"], it.get("reason"))
            for it in data["events_to_exclude"]
        ],
    )


def decode_data_with_world_reader(data: Dict) -> Tuple[WorldReader, GameDescription]:
    game = RandovaniaGame(data["game"])

    resource_database = read_resource_database(game, data["resource_database"])
    dock_weakness_database = read_dock_weakness_database(data["dock_weakness_database"], resource_database)

    world_reader = WorldReader(resource_database, dock_weakness_database)
    world_list = world_reader.read_world_list(data["worlds"])

    victory_condition = read_requirement(data["victory_condition"], resource_database)
    starting_location = AreaLocation.from_json(data["starting_location"])
    initial_states = read_initial_states(data["initial_states"], resource_database)
    minimal_logic = read_minimal_logic_db(data["minimal_logic"])

    return world_reader, GameDescription(
        game=game,
        resource_database=resource_database,
        dock_weakness_database=dock_weakness_database,
        world_list=world_list,
        victory_condition=victory_condition,
        starting_location=starting_location,
        initial_states=initial_states,
        minimal_logic=minimal_logic,
    )


def decode_data(data: Dict) -> GameDescription:
    return decode_data_with_world_reader(data)[1]


def read_split_file(dir_path: Path):
    with dir_path.joinpath("header.json").open(encoding="utf-8") as meta_file:
        data = json.load(meta_file)

    worlds = data.pop("worlds")
    data["worlds"] = []
    for world_file_name in worlds:
        with dir_path.joinpath(world_file_name).open(encoding="utf-8") as world_file:
            data["worlds"].append(json.load(world_file))

    return data
