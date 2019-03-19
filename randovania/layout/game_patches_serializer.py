import base64
import re
from typing import Dict, List, Iterator, Tuple

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder
from randovania.game_description import data_reader
from randovania.game_description.area_location import AreaLocation
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.node import PickupNode, TeleporterNode, Node
from randovania.game_description.resources import PickupAssignment, find_resource_info_with_long_name, PickupEntry, \
    ResourceDatabase, ConditionalResources
from randovania.game_description.world_list import WorldList
from randovania.layout.layout_configuration import LayoutConfiguration


class BitPackPickupEntry:
    value: PickupEntry
    database: ResourceDatabase

    def __init__(self, value: PickupEntry, database: ResourceDatabase):
        self.value = value
        self.database = database

    def bit_pack_encode(self) -> Iterator[Tuple[int, int]]:
        items = self.database.item

        yield self.value.model_index, 255
        yield from self.value.item_category.bit_pack_encode()
        yield int(any(cond.name is not None for cond in self.value.resources)), 2
        yield len(self.value.resources) - 1, 8

        for i, conditional in enumerate(self.value.resources):
            if i > 0:
                yield from bitpacking.pack_array_element(conditional.item, items)

            yield len(conditional.resources), 8
            for resource, quantity in conditional.resources:
                yield from bitpacking.pack_array_element(resource, items)
                yield quantity, 255

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, name: str, database: ResourceDatabase) -> PickupEntry:
        model_index = decoder.decode_single(255)
        item_category = ItemCategory.bit_pack_unpack(decoder)
        has_name = bool(decoder.decode_single(2))
        num_conditional = decoder.decode_single(8) + 1

        conditional_resources = []
        for i in range(num_conditional):
            item_name = None  # TODO: get the first resource name
            if i > 0:
                item_dependency = decoder.decode_element(database.item)
            else:
                item_dependency = None

            resources = []
            for _ in range(decoder.decode_single(8)):
                resource = decoder.decode_element(database.item)
                quantity = decoder.decode_single(255)
                resources.append((resource, quantity))

            if has_name:
                item_name = resources[0][0].long_name

            conditional_resources.append(ConditionalResources(
                name=item_name,
                item=item_dependency,
                resources=tuple(resources),
            ))

        return PickupEntry(
            name=name,
            model_index=model_index,
            item_category=item_category,
            resources=tuple(conditional_resources)
        )


class BitPackPickupEntryList:
    value: List[PickupEntry]
    database: ResourceDatabase

    def __init__(self, value: List[PickupEntry], database: ResourceDatabase):
        self.value = value
        self.database = database

    def bit_pack_encode(self) -> Iterator[Tuple[int, int]]:
        for entry in self.value:
            yield from BitPackPickupEntry(entry, self.database).bit_pack_encode()


def _pickup_assignment_to_item_locations(world_list: WorldList,
                                         pickup_assignment: PickupAssignment,
                                         ordered_pickups: List[PickupEntry],
                                         ) -> Dict[str, Dict[str, str]]:
    items_locations = {}

    for world in sorted(world_list.worlds, key=lambda w: w.name):
        items_in_world = {}
        items_locations[world.name] = items_in_world

        for node in sorted(world.all_nodes, key=lambda w: w.name):
            if not node.is_resource_node or not isinstance(node, PickupNode):
                continue

            if node.pickup_index in pickup_assignment:
                pickup = pickup_assignment[node.pickup_index]
                ordered_pickups.append(pickup)
                item_name = pickup.name
            else:
                item_name = "Nothing"

            items_in_world[world_list.node_name(node)] = item_name

    return items_locations


def _node_mapping_to_elevator_connection(world_list: WorldList,
                                         elevators: Dict[str, str],
                                         ) -> Dict[int, AreaLocation]:
    result = {}
    for source_name, target_node in elevators.items():
        source_node: TeleporterNode = world_list.node_from_name(source_name)
        target_node = world_list.node_from_name(target_node)

        result[source_node.teleporter_instance_id] = AreaLocation(
            world_list.nodes_to_world(target_node).world_asset_id,
            world_list.nodes_to_area(target_node).area_asset_id
        )

    return result


def _find_node_with_teleporter(world_list: WorldList, teleporter_id: int) -> Node:
    for node in world_list.all_nodes:
        if isinstance(node, TeleporterNode):
            if node.teleporter_instance_id == teleporter_id:
                return node
    raise ValueError("Unknown teleporter_id: {}".format(teleporter_id))


def serialize(patches: GamePatches, game_data: dict) -> dict:
    """
    Encodes a given GamePatches into a JSON-serializable dict.
    :param patches:
    :param game_data:
    :return:
    """
    game = data_reader.decode_data(game_data)
    world_list = game.world_list
    ordered_pickups = []

    result = {
        "starting_location": world_list.area_name(world_list.area_by_area_location(patches.starting_location)),
        "starting_items": {
            resource_info.long_name: quantity
            for resource_info, quantity in sorted(patches.extra_initial_items, key=lambda x: x[0].long_name)
        },
        "elevators": {
            world_list.area_name(world_list.nodes_to_area(_find_node_with_teleporter(world_list, teleporter_id))):
                world_list.area_name(world_list.nodes_to_area(world_list.resolve_teleporter_connection(connection)))
            for teleporter_id, connection in patches.elevator_connection.items()
        },
        "locations": {
            key: value
            for key, value in _pickup_assignment_to_item_locations(world_list,
                                                                   patches.pickup_assignment,
                                                                   ordered_pickups).items()
        },
    }

    b = bitpacking.pack_value(BitPackPickupEntryList(ordered_pickups, game.resource_database))
    result["_locations_internal"] = base64.b64encode(b).decode("utf-8")

    return result


def _area_name_to_area_location(world_list: WorldList, area_name: str) -> AreaLocation:
    world_name, area_name = re.match("([^/]+)/([^/]+)", area_name).group(1, 2)
    starting_world = world_list.world_with_name(world_name)
    starting_area = starting_world.area_by_name(area_name)
    return AreaLocation(starting_world.world_asset_id, starting_area.area_asset_id)


def decode(game_modifications: dict, configuration: LayoutConfiguration) -> GamePatches:
    """
    Decodes a dict created by `serialize` back into a GamePatches.
    :param game_modifications:
    :param configuration:
    :return:
    """
    game = data_reader.decode_data(configuration.game_data)
    world_list = game.world_list

    # Starting Location
    starting_location = _area_name_to_area_location(world_list, game_modifications["starting_location"])

    # Initial items
    extra_initial_items = tuple([
        (find_resource_info_with_long_name(game.resource_database.item, resource_name), quantity)
        for resource_name, quantity in game_modifications["starting_items"].items()
    ])

    # Elevators
    elevator_connection = {}
    for source_name, target_name in game_modifications["elevators"].items():
        source_area = _area_name_to_area_location(world_list, source_name)
        target_area = _area_name_to_area_location(world_list, target_name)

        elevator_connection[world_list.resolve_teleporter_connection(source_area).teleporter_instance_id] = target_area

    # Pickups
    pickup_assignment = {}
    decoder = BitPackDecoder(base64.b64decode(game_modifications["_locations_internal"].encode("utf-8"), validate=True))

    for world_name, world_data in game_modifications["locations"].items():
        for area_node_name, pickup_name in world_data.items():
            if pickup_name == "Nothing":
                continue

            node: PickupNode = world_list.node_from_name(f"{world_name}/{area_node_name}")
            pickup = BitPackPickupEntry.bit_pack_unpack(decoder, pickup_name, game.resource_database)
            pickup_assignment[node.pickup_index] = pickup

    return GamePatches(
        pickup_assignment=pickup_assignment,  # PickupAssignment
        elevator_connection=elevator_connection,  # Dict[int, AreaLocation]
        dock_connection={},  # Dict[Tuple[int, int], DockConnection]
        dock_weakness={},  # Dict[Tuple[int, int], DockWeakness]
        extra_initial_items=extra_initial_items,  # ResourceGainTuple
        starting_location=starting_location,  # AreaLocation
    )
