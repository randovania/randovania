import collections
import re
from typing import Dict, List, DefaultDict

from randovania.game_description import default_database
from randovania.game_description.world.area import Area
from randovania.game_description.world.area_location import AreaLocation
from randovania.game_description.assignment import PickupAssignment, PickupTarget
from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches, ElevatorConnection
from randovania.game_description.hint import Hint
from randovania.game_description.world.node import PickupNode, TeleporterNode
from randovania.game_description.resources.logbook_asset import LogbookAsset
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.search import find_resource_info_with_long_name
from randovania.game_description.resources.translator_gate import TranslatorGate
from randovania.game_description.world.teleporter import Teleporter
from randovania.game_description.world.world_list import WorldList
from randovania.games.game import RandovaniaGame
from randovania.generator.item_pool import pool_creator, PoolResults
from randovania.layout.prime2.echoes_configuration import EchoesConfiguration

_ETM_NAME = "Energy Transfer Module"


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
                item_name = f"{target.pickup.name} for Player {target.player + 1}"
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


def _find_area_with_teleporter(world_list: WorldList, teleporter: Teleporter) -> Area:
    return world_list.area_by_area_location(teleporter.area_location)


def _name_for_gate(gate: TranslatorGate) -> str:
    from randovania.games.patchers import claris_patcher
    for items in claris_patcher.decode_randomizer_data()["TranslatorLocationData"]:
        if items["Index"] == gate.index:
            return items["Name"]
    raise ValueError("Unknown gate: {}".format(gate))


def _find_gate_with_name(gate_name: str) -> TranslatorGate:
    from randovania.games.patchers import claris_patcher
    for items in claris_patcher.decode_randomizer_data()["TranslatorLocationData"]:
        if items["Name"] == gate_name:
            return TranslatorGate(items["Index"])
    raise ValueError("Unknown gate name: {}".format(gate_name))


def serialize_single(player_index: int, num_players: int, patches: GamePatches, game_enum: RandovaniaGame) -> dict:
    """
    Encodes a given GamePatches into a JSON-serializable dict.
    :param player_index:
    :param num_players:
    :param patches:
    :param game_enum:
    :return:
    """
    game = default_database.game_description_for(game_enum)
    world_list = game.world_list

    result = {
        "starting_location": world_list.area_name(world_list.area_by_area_location(patches.starting_location),
                                                  separator="/"),
        "starting_items": {
            resource_info.long_name: quantity
            for resource_info, quantity in patches.starting_items.items()
        },
        "elevators": {
            world_list.area_name(_find_area_with_teleporter(world_list, teleporter), "/"):
                world_list.area_name(world_list.area_by_area_location(connection), "/")
            for teleporter, connection in patches.elevator_connection.items()
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
    return result


def _area_name_to_area_location(world_list: WorldList, area_name: str) -> AreaLocation:
    world_name, area_name = re.match("([^/]+)/([^/]+)", area_name).group(1, 2)
    starting_world = world_list.world_with_name(world_name)
    starting_area = starting_world.area_by_name(area_name)
    return AreaLocation(starting_world.world_asset_id, starting_area.area_asset_id)


def _find_pickup_with_name(item_pool: List[PickupEntry], pickup_name: str) -> PickupEntry:
    for pickup in item_pool:
        if pickup.name == pickup_name:
            return pickup

    names = set(pickup.name for pickup in item_pool)
    raise ValueError(f"Unable to find a pickup with name {pickup_name}. Possible values: {sorted(names)}")


def decode_single(player_index: int, all_pools: Dict[int, PoolResults], game: GameDescription,
                  game_modifications: dict, configuration: EchoesConfiguration) -> GamePatches:
    """
    Decodes a dict created by `serialize` back into a GamePatches.
    :param player_index:
    :param all_pools:
    :param game:
    :param game_modifications:
    :param configuration:
    :return:
    """
    world_list = game.world_list

    initial_pickup_assignment = all_pools[player_index].assignment

    # Starting Location
    starting_location = _area_name_to_area_location(world_list, game_modifications["starting_location"])

    # Initial items
    starting_items = {
        find_resource_info_with_long_name(game.resource_database.item, resource_name): quantity
        for resource_name, quantity in game_modifications["starting_items"].items()
    }

    # Elevators
    elevator_connection: ElevatorConnection = {}
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
        elevator_connection[source_node.teleporter] = target_area

    # Translator Gates
    translator_gates = {
        _find_gate_with_name(gate_name): find_resource_info_with_long_name(game.resource_database.item, resource_name)
        for gate_name, resource_name in game_modifications["translators"].items()
    }

    # Pickups
    target_name_re = re.compile(r"(.*) for Player (\d+)")

    pickup_assignment: PickupAssignment = {}
    for world_name, world_data in game_modifications["locations"].items():
        for area_node_name, target_name in world_data.items():
            if target_name == _ETM_NAME:
                continue

            pickup_name_match = target_name_re.match(target_name)
            if pickup_name_match is not None:
                pickup_name = pickup_name_match.group(1)
                target_player = int(pickup_name_match.group(2)) - 1
            else:
                pickup_name = target_name
                target_player = 0

            node = world_list.node_from_name(f"{world_name}/{area_node_name}")
            assert isinstance(node, PickupNode)
            if node.pickup_index in initial_pickup_assignment:
                pickup = initial_pickup_assignment[node.pickup_index]
                if (pickup_name, target_player) != (pickup.name, player_index):
                    raise ValueError(f"{area_node_name} should be vanilla based on configuration")

            elif pickup_name != _ETM_NAME:
                configuration_item_pool = all_pools[target_player].pickups
                pickup = _find_pickup_with_name(configuration_item_pool, pickup_name)
                configuration_item_pool.remove(pickup)
            else:
                pickup = None

            if pickup is not None:
                pickup_assignment[node.pickup_index] = PickupTarget(pickup, target_player)

    # Hints
    hints = {}
    for asset_id, hint in game_modifications["hints"].items():
        hints[LogbookAsset(int(asset_id))] = Hint.from_json(hint)

    return GamePatches(
        player_index=player_index,
        pickup_assignment=pickup_assignment,  # PickupAssignment
        elevator_connection=elevator_connection,  # ElevatorConnection
        dock_connection={},  # Dict[Tuple[int, int], DockConnection]
        dock_weakness={},  # Dict[Tuple[int, int], DockWeakness]
        translator_gates=translator_gates,
        starting_items=starting_items,  # ResourceGainTuple
        starting_location=starting_location,  # AreaLocation
        hints=hints,
    )


def decode(game_modifications: List[dict],
           layout_configurations: Dict[int, EchoesConfiguration],
           ) -> Dict[int, GamePatches]:
    all_games = {index: default_database.game_description_for(configuration.game)
                 for index, configuration in layout_configurations.items()}
    all_pools = {index: pool_creator.calculate_pool_results(configuration, all_games[index].resource_database)
                 for index, configuration in layout_configurations.items()}
    return {
        index: decode_single(index, all_pools, all_games[index], modifications, layout_configurations[index])
        for index, modifications in enumerate(game_modifications)
    }


def serialize(all_patches: Dict[int, GamePatches], all_games: Dict[int, RandovaniaGame]) -> List[dict]:
    return [
        serialize_single(index, len(all_patches), patches, all_games[index])
        for index, patches in all_patches.items()
    ]
