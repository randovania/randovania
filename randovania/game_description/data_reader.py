from typing import List, Callable, TypeVar, Tuple, Dict

from randovania.game_description.area import Area
from randovania.game_description.area_location import AreaLocation
from randovania.game_description.dock import DockWeakness, DockType, DockWeaknessDatabase, DockConnection
from randovania.game_description.game_description import GameDescription
from randovania.game_description.echoes_game_specific import EchoesBeamConfiguration, EchoesGameSpecific
from randovania.game_description.node import GenericNode, DockNode, TeleporterNode, PickupNode, EventNode, Node, \
    TranslatorGateNode, LogbookNode, LoreType
from randovania.game_description.requirements import ResourceRequirement, Requirement, \
    RequirementOr, RequirementAnd
from randovania.game_description.resources.damage_resource_info import DamageReduction, DamageResourceInfo
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_database import find_resource_info_with_id, ResourceDatabase, \
    find_resource_info_with_long_name
from randovania.game_description.resources.resource_info import ResourceInfo, ResourceGainTuple
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo
from randovania.game_description.resources.translator_gate import TranslatorGate
from randovania.game_description.world import World
from randovania.game_description.world_list import WorldList

X = TypeVar('X')
Y = TypeVar('Y')


def read_array(data: List[Y], item_reader: Callable[[Y], X]) -> List[X]:
    return [item_reader(item) for item in data]


def read_resource_info(data: Dict, resource_type: ResourceType) -> SimpleResourceInfo:
    return SimpleResourceInfo(data["index"], data["long_name"],
                              data["short_name"], resource_type)


def read_resource_info_array(data: List[Dict], resource_type: ResourceType) -> List[SimpleResourceInfo]:
    return read_array(data, lambda info: read_resource_info(info, resource_type=resource_type))


# Damage

def read_damage_reduction(data: Dict, items: List[SimpleResourceInfo]) -> DamageReduction:
    return DamageReduction(find_resource_info_with_id(items, data["index"]),
                           data["multiplier"])


def read_damage_reductions(data: List[Dict], items: List[SimpleResourceInfo]) -> Tuple[DamageReduction, ...]:
    return tuple(read_array(data, lambda info: read_damage_reduction(info, items)))


def read_damage_resource_info(data: Dict, items: List[SimpleResourceInfo]) -> DamageResourceInfo:
    return DamageResourceInfo(data["index"], data["long_name"],
                              data["short_name"],
                              read_damage_reductions(data["reductions"], items))


def read_damage_resource_info_array(data: List[Dict], items: List[SimpleResourceInfo]) -> List[DamageResourceInfo]:
    return read_array(data, lambda info: read_damage_resource_info(info, items))


# Requirement


def read_resource_requirement(data: Dict, resource_database: ResourceDatabase
                              ) -> ResourceRequirement:
    data = data["data"]
    return ResourceRequirement.with_data(
        resource_database,
        ResourceType(data["type"]), data["index"],
        data["amount"], data["negate"])


def read_requirement_and(data: Dict,
                         resource_database: ResourceDatabase,
                         ) -> RequirementAnd:
    return RequirementAnd([
        read_requirement(item, resource_database)
        for item in data["data"]
    ])


def read_requirement_or(data: Dict,
                        resource_database: ResourceDatabase) -> RequirementOr:
    return RequirementOr([
        read_requirement(item, resource_database)
        for item in data["data"]
    ])


def read_requirement(data: Dict, resource_database: ResourceDatabase) -> Requirement:
    req_type = data["type"]
    if req_type == "resource":
        return read_resource_requirement(data, resource_database)

    elif req_type == "and":
        return read_requirement_and(data, resource_database)

    elif req_type == "or":
        return read_requirement_or(data, resource_database)

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
                        item["is_blast_door"],
                        read_requirement(item["requirement"], resource_database),
                        dock_type)


def read_dock_weakness_database(data: Dict,
                                resource_database: ResourceDatabase,
                                ) -> DockWeaknessDatabase:
    door_types = read_array(data["door"], lambda item: read_dock_weakness(item, resource_database, DockType.DOOR))
    portal_types = read_array(data["portal"], lambda item: read_dock_weakness(item, resource_database, DockType.PORTAL))

    return DockWeaknessDatabase(
        door=door_types,
        morph_ball=[
            DockWeakness(0, "Morph Ball Door", False, Requirement.trivial(), DockType.MORPH_BALL_DOOR)
        ],
        other=[
            DockWeakness(0, "Other Door", False, Requirement.trivial(), DockType.OTHER)
        ],
        portal=portal_types)


def read_beam_configuration(data: Dict, resource_database: ResourceDatabase,
                            ) -> EchoesBeamConfiguration:
    return EchoesBeamConfiguration(
        item=resource_database.get_item(data["item_index"]),
        ammo_a=resource_database.get_item(data["ammo_a"]) if data["ammo_a"] is not None else None,
        ammo_b=resource_database.get_item(data["ammo_b"]) if data["ammo_b"] is not None else None,
        uncharged_cost=data["uncharged_cost"],
        charged_cost=data["charged_cost"],
        combo_missile_cost=data["combo_missile_cost"],
        combo_ammo_cost=data["combo_ammo_cost"],
    )


def read_game_specific(data: Dict, resource_database: ResourceDatabase,
                       ) -> EchoesGameSpecific:
    return EchoesGameSpecific(
        energy_per_tank=data["energy_per_tank"],
        beam_configurations=tuple(
            read_beam_configuration(beam, resource_database)
            for beam in data["beam_configurations"]
        )
    )


class WorldReader:
    resource_database: ResourceDatabase
    dock_weakness_database: DockWeaknessDatabase
    generic_index: int = -1

    def __init__(self,
                 resource_database: ResourceDatabase,
                 dock_weakness_database: DockWeaknessDatabase,
                 ):

        self.resource_database = resource_database
        self.dock_weakness_database = dock_weakness_database

    def read_node(self, data: Dict) -> Node:
        name: str = data["name"]
        heal: bool = data["heal"]
        node_type: int = data["node_type"]
        self.generic_index += 1

        if node_type == "generic":
            return GenericNode(name, heal, self.generic_index)

        elif node_type == "dock":
            return DockNode(name, heal, self.generic_index, data["dock_index"],
                            DockConnection(data["connected_area_asset_id"], data["connected_dock_index"]),
                            self.dock_weakness_database.get_by_type_and_index(DockType(data["dock_type"]),
                                                                              data["dock_weakness_index"]))

        elif node_type == "pickup":
            return PickupNode(name, heal, self.generic_index, PickupIndex(data["pickup_index"]), data["major_location"])

        elif node_type == "teleporter":
            instance_id = data["teleporter_instance_id"]

            destination_world_asset_id = data["destination_world_asset_id"]
            destination_area_asset_id = data["destination_area_asset_id"]

            return TeleporterNode(name, heal, self.generic_index, instance_id,
                                  AreaLocation(destination_world_asset_id, destination_area_asset_id),
                                  data["scan_asset_id"],
                                  data["keep_name_when_vanilla"],
                                  data["editable"],
                                  )

        elif node_type == "event":
            return EventNode(name, heal, self.generic_index,
                             self.resource_database.get_by_type_and_index(ResourceType.EVENT, data["event_index"]))

        elif node_type == "translator_gate":
            return TranslatorGateNode(name, heal, self.generic_index,
                                      TranslatorGate(data["gate_index"]),
                                      find_resource_info_with_long_name(
                                          self.resource_database.item,
                                          "Scan Visor"
                                      ))

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

            return LogbookNode(name, heal, self.generic_index, data["string_asset_id"],
                               find_resource_info_with_long_name(
                                   self.resource_database.item,
                                   "Scan Visor"
                               ),
                               lore_type,
                               required_translator,
                               hint_index)

        else:
            raise Exception("Unknown node type: {}".format(node_type))

    def read_area(self, data: Dict) -> Area:
        nodes = read_array(data["nodes"], self.read_node)
        nodes_by_name = {node.name: node for node in nodes}

        connections = {}
        for i, origin_data in enumerate(data["nodes"]):
            origin = nodes[i]
            connections[origin] = {}

            for target_name, target_requirement in origin_data["connections"].items():
                the_set = read_requirement(target_requirement, self.resource_database)

                if the_set != Requirement.impossible():
                    connections[origin][nodes_by_name[target_name]] = the_set

        return Area(data["name"], data["in_dark_aether"], data["asset_id"], data["default_node_index"],
                    nodes, connections)

    def read_area_list(self, data: List[Dict]) -> List[Area]:
        return read_array(data, self.read_area)

    def read_world(self, data: Dict) -> World:
        return World(data["name"], data["dark_name"], data["asset_id"],
                     self.read_area_list(data["areas"]))

    def read_world_list(self, data: List[Dict]) -> WorldList:
        return WorldList(read_array(data, self.read_world))


def read_resource_database(data: Dict) -> ResourceDatabase:
    item = read_resource_info_array(data["items"], ResourceType.ITEM)
    return ResourceDatabase(
        item=item,
        event=read_resource_info_array(data["events"], ResourceType.EVENT),
        trick=read_resource_info_array(data["tricks"], ResourceType.TRICK),
        damage=read_damage_resource_info_array(data["damage"], item),
        version=read_resource_info_array(data["versions"], ResourceType.VERSION),
        misc=read_resource_info_array(data["misc"], ResourceType.MISC),
        difficulty=read_resource_info_array(data["difficulty"], ResourceType.DIFFICULTY),
    )


def read_initial_states(data: Dict[str, List], resource_database: ResourceDatabase) -> Dict[str, ResourceGainTuple]:
    return {
        name: read_resource_gain_tuple(item, resource_database)
        for name, item in data.items()
    }


def decode_data_with_world_reader(data: Dict) -> Tuple[WorldReader, GameDescription]:
    game = data["game"]
    game_name = data["game_name"]

    resource_database = read_resource_database(data["resource_database"])
    dock_weakness_database = read_dock_weakness_database(data["dock_weakness_database"], resource_database)
    game_specific = read_game_specific(data["game_specific"], resource_database)

    world_reader = WorldReader(resource_database, dock_weakness_database)
    world_list = world_reader.read_world_list(data["worlds"])

    victory_condition = read_requirement(data["victory_condition"], resource_database)
    starting_location = AreaLocation.from_json(data["starting_location"])
    initial_states = read_initial_states(data["initial_states"], resource_database)

    return world_reader, GameDescription(
        game=game,
        game_name=game_name,
        resource_database=resource_database,
        game_specific=game_specific,
        dock_weakness_database=dock_weakness_database,
        world_list=world_list,
        victory_condition=victory_condition,
        starting_location=starting_location,
        initial_states=initial_states,
    )


def decode_data(data: Dict) -> GameDescription:
    return decode_data_with_world_reader(data)[1]
