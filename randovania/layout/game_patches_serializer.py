import base64
import collections
import dataclasses
import re
from typing import Dict, List, Iterator, Tuple, DefaultDict

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder, BitPackValue, BitPackFloat
from randovania.game_description import data_reader
from randovania.game_description.area_location import AreaLocation
from randovania.game_description.assignment import PickupAssignment, PickupTarget
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.hint import Hint
from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.node import PickupNode, TeleporterNode, Node
from randovania.game_description.resources.logbook_asset import LogbookAsset
from randovania.game_description.resources.pickup_entry import ConditionalResources, ResourceConversion, \
    MAXIMUM_PICKUP_CONDITIONAL_RESOURCES, MAXIMUM_PICKUP_RESOURCES, MAXIMUM_PICKUP_CONVERSION, PickupEntry
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_database import find_resource_info_with_long_name, ResourceDatabase
from randovania.game_description.resources.translator_gate import TranslatorGate
from randovania.game_description.world_list import WorldList
from randovania.games.prime import default_data
from randovania.layout.layout_configuration import LayoutConfiguration

_ETM_NAME = "Energy Transfer Module"
_PROBABILITY_OFFSET_META = {
    "min": -3,
    "max": 3,
    "precision": 2.0,
    "if_different": 0.0,
}


class BitPackPickupEntry:
    value: PickupEntry
    database: ResourceDatabase

    def __init__(self, value: PickupEntry, database: ResourceDatabase):
        self.value = value
        self.database = database

    def bit_pack_encode(self, metadata) -> Iterator[Tuple[int, int]]:
        items = self.database.item
        has_name = any(cond.name is not None for cond in self.value.resources)

        yield self.value.model_index, 255
        yield from BitPackFloat(self.value.probability_offset).bit_pack_encode(_PROBABILITY_OFFSET_META)
        yield from self.value.item_category.bit_pack_encode({})
        yield from bitpacking.encode_bool(has_name)
        yield len(self.value.resources) - 1, MAXIMUM_PICKUP_CONDITIONAL_RESOURCES

        for i, conditional in enumerate(self.value.resources):
            if i > 0:
                yield from bitpacking.pack_array_element(conditional.item, items)

            yield len(conditional.resources), MAXIMUM_PICKUP_RESOURCES + 1
            for resource, quantity in conditional.resources:
                yield from bitpacking.pack_array_element(resource, items)
                yield quantity, 255

            if has_name:
                yield from bitpacking.encode_bool(conditional.name == self.value.name)

        yield len(self.value.convert_resources), MAXIMUM_PICKUP_CONVERSION + 1
        for conversion in self.value.convert_resources:
            yield from bitpacking.pack_array_element(conversion.source, items)
            yield from bitpacking.pack_array_element(conversion.target, items)

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, name: str, database: ResourceDatabase) -> PickupEntry:
        model_index = decoder.decode_single(255)
        probability_offset = BitPackFloat.bit_pack_unpack(decoder, _PROBABILITY_OFFSET_META)
        item_category = ItemCategory.bit_pack_unpack(decoder, {})
        has_name = bitpacking.decode_bool(decoder)
        num_conditional = decoder.decode_single(MAXIMUM_PICKUP_CONDITIONAL_RESOURCES) + 1

        conditional_resources = []
        for i in range(num_conditional):
            item_name = None  # TODO: get the first resource name
            if i > 0:
                item_dependency = decoder.decode_element(database.item)
            else:
                item_dependency = None

            resources = []
            for _ in range(decoder.decode_single(MAXIMUM_PICKUP_RESOURCES + 1)):
                resource = decoder.decode_element(database.item)
                quantity = decoder.decode_single(255)
                resources.append((resource, quantity))

            if has_name:
                if bitpacking.decode_bool(decoder):
                    item_name = name
                else:
                    item_name = resources[0][0].long_name

            conditional_resources.append(ConditionalResources(
                name=item_name,
                item=item_dependency,
                resources=tuple(resources),
            ))

        num_convert = decoder.decode_single(MAXIMUM_PICKUP_CONVERSION + 1)
        convert_resources = []
        for i in range(num_convert):
            source = decoder.decode_element(database.item)
            target = decoder.decode_element(database.item)
            convert_resources.append(ResourceConversion(source, target))

        return PickupEntry(
            name=name,
            model_index=model_index,
            item_category=item_category,
            resources=tuple(conditional_resources),
            convert_resources=tuple(convert_resources),
            probability_offset=probability_offset,
        )


class BitPackPickupEntryList(BitPackValue):
    value: List[Tuple[PickupIndex, PickupTarget]]
    num_players: int
    database: ResourceDatabase

    def __init__(self, value: List[Tuple[PickupIndex, PickupTarget]], num_players: int, database: ResourceDatabase):
        self.value = value
        self.num_players = num_players
        self.database = database

    def bit_pack_encode(self, metadata) -> Iterator[Tuple[int, int]]:
        for index, entry in self.value:
            yield index.index, 255
            yield from bitpacking.encode_int_with_limits(entry.player, (self.num_players,))
            yield from BitPackPickupEntry(entry.pickup, self.database).bit_pack_encode({})

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, metadata) -> "BitPackPickupEntryList":
        result = []
        index_mapping = metadata["index_mapping"]
        num_players = metadata["num_players"]

        for _ in range(len(index_mapping)):
            index = PickupIndex(decoder.decode_single(255))
            target_player = bitpacking.decode_int_with_limits(decoder, (num_players,))
            pickup = BitPackPickupEntry.bit_pack_unpack(decoder, index_mapping[index], metadata["database"])
            result.append((index, PickupTarget(pickup, target_player)))

        return BitPackPickupEntryList(result, num_players, metadata["database"])


def _pickup_assignment_to_item_locations(world_list: WorldList,
                                         pickup_assignment: PickupAssignment,
                                         num_players: int,
                                         ) -> Dict[str, Dict[str, str]]:
    items_locations: DefaultDict[str, Dict[str, str]] = collections.defaultdict(dict)

    for world, area, node in world_list.all_worlds_areas_nodes:
        if not node.is_resource_node or not isinstance(node, PickupNode):
            continue

        if node.pickup_index in pickup_assignment:
            target = pickup_assignment[node.pickup_index]
            if num_players > 1:
                item_name = f"{target.pickup.name} for Player {target.player}"
            else:
                item_name = f"{target.pickup.name}"
        else:
            item_name = _ETM_NAME

        world_name = world.dark_name if area.in_dark_aether else world.name
        items_locations[world_name][world_list.node_name(node)] = item_name

    return {
        world: {
            area: item
            for area, item in sorted(items_locations[world].items())
        }
        for world in sorted(items_locations.keys())
    }


def _node_mapping_to_elevator_connection(world_list: WorldList,
                                         elevators: Dict[str, str],
                                         ) -> Dict[int, AreaLocation]:
    result = {}
    for source_name, target_node in elevators.items():
        source_node = world_list.node_from_name(source_name)
        assert isinstance(source_node, TeleporterNode)

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


def _name_for_gate(gate: TranslatorGate) -> str:
    for items in default_data.decode_randomizer_data()["TranslatorLocationData"]:
        if items["Index"] == gate.index:
            return items["Name"]
    raise ValueError("Unknown gate: {}".format(gate))


def _find_gate_with_name(gate_name: str) -> TranslatorGate:
    for items in default_data.decode_randomizer_data()["TranslatorLocationData"]:
        if items["Name"] == gate_name:
            return TranslatorGate(items["Index"])
    raise ValueError("Unknown gate name: {}".format(gate_name))


def serialize_single(player_index: int, num_players: int, patches: GamePatches, game_data: dict) -> dict:
    """
    Encodes a given GamePatches into a JSON-serializable dict.
    :param player_index:
    :param num_players:
    :param patches:
    :param game_data:
    :return:
    """
    game = data_reader.decode_data(game_data)
    world_list = game.world_list

    result = {
        "starting_location": world_list.area_name(world_list.area_by_area_location(patches.starting_location), True),
        "starting_items": {
            resource_info.long_name: quantity
            for resource_info, quantity in patches.starting_items.items()
        },
        "elevators": {
            world_list.area_name(world_list.nodes_to_area(_find_node_with_teleporter(world_list,
                                                                                     teleporter_id)), True):
                world_list.area_name(world_list.nodes_to_area(world_list.resolve_teleporter_connection(connection)),
                                     True)
            for teleporter_id, connection in patches.elevator_connection.items()
        },
        "translators": {
            _name_for_gate(gate): requirement.long_name
            for gate, requirement in patches.translator_gates.items()
        },
        "locations": {
            key: value
            for key, value in _pickup_assignment_to_item_locations(world_list,
                                                                   patches.pickup_assignment,
                                                                   num_players).items()
        },
        "hints": {
            str(asset.asset_id): hint.as_json
            for asset, hint in patches.hints.items()
        }
    }

    b = bitpacking.pack_value(BitPackPickupEntryList(list(patches.pickup_assignment.items()),
                                                     num_players,
                                                     game.resource_database))
    result["_locations_internal"] = base64.b64encode(b).decode("utf-8")

    return result


def _area_name_to_area_location(world_list: WorldList, area_name: str) -> AreaLocation:
    world_name, area_name = re.match("([^/]+)/([^/]+)", area_name).group(1, 2)
    starting_world = world_list.world_with_name(world_name)
    starting_area = starting_world.area_by_name(area_name)
    return AreaLocation(starting_world.world_asset_id, starting_area.area_asset_id)


def decode_single(player_index: int, num_players: int, game_modifications: dict,
                  configuration: LayoutConfiguration) -> GamePatches:
    """
    Decodes a dict created by `serialize` back into a GamePatches.
    :param game_modifications:
    :param player_index:
    :param num_players:
    :param configuration:
    :return:
    """
    game = data_reader.decode_data(configuration.game_data)
    game_specific = dataclasses.replace(
        game.game_specific,
        energy_per_tank=configuration.energy_per_tank,
        beam_configurations=configuration.beam_configuration.create_game_specific(game.resource_database))

    world_list = game.world_list

    # Starting Location
    starting_location = _area_name_to_area_location(world_list, game_modifications["starting_location"])

    # Initial items
    starting_items = {
        find_resource_info_with_long_name(game.resource_database.item, resource_name): quantity
        for resource_name, quantity in game_modifications["starting_items"].items()
    }

    # Elevators
    elevator_connection = {}
    for source_name, target_name in game_modifications["elevators"].items():
        source_area = _area_name_to_area_location(world_list, source_name)
        target_area = _area_name_to_area_location(world_list, target_name)

        potential_source_nodes = [
            node
            for node in world_list.area_by_area_location(source_area).nodes
            if isinstance(node, TeleporterNode)
        ]
        assert len(potential_source_nodes) == 1
        source_node = potential_source_nodes[0]
        elevator_connection[source_node.teleporter_instance_id] = target_area

    # Translator Gates
    translator_gates = {
        _find_gate_with_name(gate_name): find_resource_info_with_long_name(game.resource_database.item, resource_name)
        for gate_name, resource_name in game_modifications["translators"].items()
    }

    # Pickups
    target_name_re = re.compile(r"(.*) for Player \d+")

    index_to_pickup_name = {}
    for world_name, world_data in game_modifications["locations"].items():
        for area_node_name, target_name in world_data.items():
            if target_name == _ETM_NAME:
                continue

            pickup_name_match = target_name_re.match(target_name)
            if pickup_name_match is not None:
                pickup_name = pickup_name_match.group(1)
            else:
                pickup_name = target_name

            node = world_list.node_from_name(f"{world_name}/{area_node_name}")
            assert isinstance(node, PickupNode)
            index_to_pickup_name[node.pickup_index] = pickup_name

    decoder = BitPackDecoder(base64.b64decode(game_modifications["_locations_internal"].encode("utf-8"), validate=True))
    pickup_assignment = dict(BitPackPickupEntryList.bit_pack_unpack(decoder, {
        "index_mapping": index_to_pickup_name,
        "num_players": num_players,
        "database": game.resource_database,
    }).value)

    # Hints
    hints = {}
    for asset_id, hint in game_modifications["hints"].items():
        hints[LogbookAsset(int(asset_id))] = Hint.from_json(hint)

    return GamePatches(
        player_index=player_index,
        pickup_assignment=pickup_assignment,  # PickupAssignment
        elevator_connection=elevator_connection,  # Dict[int, AreaLocation]
        dock_connection={},  # Dict[Tuple[int, int], DockConnection]
        dock_weakness={},  # Dict[Tuple[int, int], DockWeakness]
        translator_gates=translator_gates,
        starting_items=starting_items,  # ResourceGainTuple
        starting_location=starting_location,  # AreaLocation
        hints=hints,
        game_specific=game_specific,
    )


def decode(game_modifications: List[dict],
           layout_configurations: Dict[int, LayoutConfiguration],
           ) -> Dict[int, GamePatches]:
    return {
        index: decode_single(index, len(game_modifications), modifications, layout_configurations[index])
        for index, modifications in enumerate(game_modifications)
    }


def serialize(all_patches: Dict[int, GamePatches], all_game_data: Dict[int, dict]) -> List[dict]:
    return [
        serialize_single(index, len(all_patches), patches, all_game_data[index])
        for index, patches in all_patches.items()
    ]
