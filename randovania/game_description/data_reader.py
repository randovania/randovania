from typing import List, Callable, TypeVar, Tuple, Dict, Optional

from randovania.game_description.dock import DockWeakness, DockType, DockWeaknessDatabase
from randovania.game_description.echoes_elevator import Elevator
from randovania.game_description.game_description import World, Area, GameDescription
from randovania.game_description.node import GenericNode, DockNode, TeleporterNode, PickupNode, EventNode, Node, \
    is_resource_node
from randovania.game_description.requirements import IndividualRequirement, RequirementList, RequirementSet
from randovania.game_description.resources import SimpleResourceInfo, DamageReduction, DamageResourceInfo, PickupIndex, \
    ResourceGain, PickupEntry, find_resource_info_with_long_name, ResourceType, ResourceDatabase, PickupDatabase, \
    find_resource_info_with_id

X = TypeVar('X')
Y = TypeVar('Y')


def read_array(data: List[Y], item_reader: Callable[[Y], X]) -> List[X]:
    return [item_reader(item) for item in data]


def read_resource_info(data: Dict, resource_type: str = "") -> SimpleResourceInfo:
    return SimpleResourceInfo(data["index"], data["long_name"],
                              data["short_name"], resource_type)


def read_resource_info_array(data: List[Dict], resource_type: str = "") -> List[SimpleResourceInfo]:
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


# Pickup

def read_pickup_info_array(data: List[Dict],
                           resource_database: ResourceDatabase) -> List[PickupEntry]:
    return read_array(data, lambda pickup: PickupEntry.from_data(pickup, resource_database))


# Requirement


def read_individual_requirement(data: Dict, resource_database: ResourceDatabase
                                ) -> IndividualRequirement:
    return IndividualRequirement.with_data(
        resource_database,
        ResourceType(data["requirement_type"]), data["requirement_index"],
        data["amount"], data["negate"])


def read_requirement_list(data: List[Dict],
                          resource_database: ResourceDatabase,
                          ) -> Optional[RequirementList]:

    individuals = read_array(data, lambda x: read_individual_requirement(x, resource_database=resource_database))
    return RequirementList.without_misc_resources(individuals, resource_database)


def read_requirement_set(data: List[List[Dict]],
                         resource_database: ResourceDatabase) -> RequirementSet:

    alternatives = read_array(data, lambda x: read_requirement_list(x, resource_database=resource_database))
    return RequirementSet(alternative for alternative in alternatives if alternative is not None)


# Dock Weakness


def read_dock_weakness_database(data: Dict,
                                resource_database: ResourceDatabase,
                                ) -> DockWeaknessDatabase:

    def read_dock_weakness(item: Dict) -> DockWeakness:
        return DockWeakness(item["index"], item["name"], item["is_blast_door"],
                            read_requirement_set(item["requirement_set"], resource_database))

    door_types = read_array(data["door"], read_dock_weakness)
    portal_types = read_array(data["portal"], read_dock_weakness)
    return DockWeaknessDatabase(
        door=door_types,
        morph_ball=[
            DockWeakness(0, "Morph Ball Door", False, RequirementSet.trivial())
        ],
        other=[DockWeakness(0, "Other Door", False, RequirementSet.trivial())],
        portal=portal_types)


class WorldReader:
    resource_database: ResourceDatabase
    dock_weakness_database: DockWeaknessDatabase
    elevators: Dict[int, Elevator]
    generic_index: int = 0

    def __init__(self,
                 resource_database: ResourceDatabase,
                 dock_weakness_database: DockWeaknessDatabase,
                 elevators: List[Elevator],
                 add_self_as_requirement_to_resources: bool):
        self.resource_database = resource_database
        self.dock_weakness_database = dock_weakness_database
        self.elevators = {
            elevator.instance_id: elevator
            for elevator in elevators
        }
        self.add_self_as_requirement_to_resources = add_self_as_requirement_to_resources

    def read_node(self, data: Dict) -> Node:
        name: str = data["name"]
        heal: bool = data["heal"]
        node_type: int = data["node_type"]

        if node_type == 0:
            self.generic_index += 1
            return GenericNode(name, heal, self.generic_index)

        elif node_type == 1:
            return DockNode(
                name, heal, data["dock_index"],
                data["connected_area_asset_id"], data["connected_dock_index"],
                self.dock_weakness_database.get_by_type_and_index(
                    DockType(data["dock_type"]), data["dock_weakness_index"]))

        elif node_type == 2:
            return PickupNode(name, heal, PickupIndex(data["pickup_index"]))

        elif node_type == 3:
            instance_id = data["teleporter_instance_id"]
            if instance_id in self.elevators:
                elevator = self.elevators[instance_id]
                destination_world_asset_id = elevator.connected_elevator.world_asset_id
                destination_area_asset_id = elevator.connected_elevator.area_asset_id
            else:
                destination_world_asset_id = data["destination_world_asset_id"]
                destination_area_asset_id = data["destination_area_asset_id"]

            return TeleporterNode(name, heal,
                                  destination_world_asset_id,
                                  destination_area_asset_id,
                                  instance_id)

        elif node_type == 4:
            return EventNode(name, heal,
                             self.resource_database.get_by_type_and_index(ResourceType.EVENT, data["event_index"]))

        else:
            raise Exception("Unknown node type: {}".format(node_type))

    def read_area(self, data: Dict) -> Area:
        name = data["name"]
        nodes = read_array(data["nodes"], self.read_node)
        nodes_by_name = {node.name: node for node in nodes}

        connections = {}
        for i, origin_data in enumerate(data["nodes"]):
            origin = nodes[i]
            connections[origin] = {}

            extra_requirement = None
            if is_resource_node(origin) and self.add_self_as_requirement_to_resources:
                extra_requirement = RequirementList.with_single_resource(origin.resource())

            for target_name, target_requirements in origin_data["connections"].items():
                the_set = read_requirement_set(target_requirements, self.resource_database)
                if extra_requirement is not None:
                    the_set = the_set.union(RequirementSet([extra_requirement]))

                if the_set != RequirementSet.impossible():
                    connections[origin][nodes_by_name[target_name]] = the_set

        return Area(name, data["asset_id"], data["default_node_index"], nodes,
                    connections)

    def read_area_list(self, data: List[Dict]) -> List[Area]:
        return read_array(data, self.read_area)

    def read_world(self, data: Dict) -> World:
        return World(data["name"], data["asset_id"],
                     self.read_area_list(data["areas"]))

    def read_world_list(self, data: List[Dict]) -> List[World]:
        return read_array(data, self.read_world)


def read_resource_database(data: Dict) -> ResourceDatabase:
    item = read_resource_info_array(data["items"], "I")
    return ResourceDatabase(
        item=item,
        event=read_resource_info_array(data["events"], "E"),
        trick=read_resource_info_array(data["tricks"], "T"),
        damage=read_damage_resource_info_array(data["damage"], item),
        version=read_resource_info_array(data["versions"]),
        misc=read_resource_info_array(data["misc"]),
        difficulty=read_resource_info_array(data["difficulty"]),
    )


def read_pickup_database(data: Dict,
                         resource_database: ResourceDatabase) -> PickupDatabase:
    return PickupDatabase(
        pickups=read_pickup_info_array(data["pickups"], resource_database),
    )


def _convert_to_resource_gain(data: Dict[str, int], resource_database: ResourceDatabase) -> ResourceGain:
    return [
        (find_resource_info_with_long_name(resource_database.item, resource_long_name), quantity)
        for resource_long_name, quantity in data.items()
    ]


def decode_data(data: Dict,
                elevators: List[Elevator],
                add_self_as_requirement_to_resources: bool = True,
                ) -> GameDescription:
    game = data["game"]
    game_name = data["game_name"]

    resource_database = read_resource_database(data["resource_database"])
    pickup_database = read_pickup_database(data, resource_database)
    dock_weakness_database = read_dock_weakness_database(data["dock_weakness_database"], resource_database)

    worlds = WorldReader(resource_database,
                         dock_weakness_database,
                         elevators,
                         add_self_as_requirement_to_resources).read_world_list(data["worlds"])

    starting_world_asset_id = data["starting_world_asset_id"]
    starting_area_asset_id = data["starting_area_asset_id"]
    victory_condition = read_requirement_set(data["victory_condition"], resource_database)
    starting_items = _convert_to_resource_gain(data["starting_items"], resource_database)
    item_loss_items = _convert_to_resource_gain(data["item_loss_items"], resource_database)

    return GameDescription(
        game=game,
        game_name=game_name,
        resource_database=resource_database,
        pickup_database=pickup_database,
        dock_weakness_database=dock_weakness_database,
        worlds=worlds,
        victory_condition=victory_condition,
        starting_world_asset_id=starting_world_asset_id,
        starting_area_asset_id=starting_area_asset_id,
        starting_items=starting_items,
        item_loss_items=item_loss_items,
    )
