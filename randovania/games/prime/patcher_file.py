from random import Random
from typing import Dict, List, Iterator

import randovania
from randovania.game_description import data_reader
from randovania.game_description.area_location import AreaLocation
from randovania.game_description.assignment import GateAssignment, PickupTarget
from randovania.game_description.default_database import default_prime2_memo_data
from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.node import TeleporterNode, PickupNode
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import ResourceGainTuple, ResourceGain, CurrentResources, \
    ResourceInfo
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.world_list import WorldList
from randovania.games.prime.patcher_file_lib import sky_temple_key_hint, item_hints
from randovania.generator.item_pool import pickup_creator, pool_creator
from randovania.interface_common.cosmetic_patches import CosmeticPatches
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.layout.hint_configuration import HintConfiguration, SkyTempleKeyHintMode
from randovania.layout.echoes_configuration import EchoesConfiguration
from randovania.layout.elevators import LayoutElevators
from randovania.layout.layout_description import LayoutDescription
from randovania.layout.pickup_model import PickupModelStyle, PickupModelDataSource

_EASTER_EGG_RUN_VALIDATED_CHANCE = 1024
_EASTER_EGG_SHINY_MISSILE = 8192
_CUSTOM_NAMES_FOR_ELEVATORS = {
    # Great Temple
    408633584: "Temple Transport Emerald",
    2399252740: "Temple Transport Violet",
    2556480432: "Temple Transport Amber",

    # Temple Grounds to Great Temple
    1345979968: "Sanctuary Quadrant",
    1287880522: "Agon Quadrant",
    2918020398: "Torvus Quadrant",

    # Temple Grounds to Areas
    1660916974: "Agon Gate",
    2889020216: "Torvus Gate",
    3455543403: "Sanctuary Gate",

    # Agon
    1473133138: "Agon Entrance",
    2806956034: "Agon Portal Access",
    3331021649: "Agon Temple Access",

    # Torvus
    1868895730: "Torvus Entrance",
    3479543630: "Torvus Temple Access",
    3205424168: "Lower Torvus Access",

    # Sanctuary
    3528156989: "Sanctuary Entrance",
    900285955: "Sanctuary Spider side",
    3145160350: "Sanctuary Vault side",
}

_RESOURCE_NAME_TRANSLATION = {
    'Temporary Missile': 'Missile',
    'Temporary Power Bombs': 'Power Bomb',
}


def _resource_user_friendly_name(resource: ResourceInfo) -> str:
    """
    Gets a name that we should display to the user for the given resource.
    :param resource:
    :return:
    """
    return _RESOURCE_NAME_TRANSLATION.get(resource.long_name, resource.long_name)


def _create_spawn_point_field(patches: GamePatches,
                              resource_database: ResourceDatabase,
                              ) -> dict:
    capacities = [
        {
            "index": item.index,
            "amount": patches.starting_items.get(item, 0),
        }
        for item in resource_database.item
    ]

    return {
        "location": patches.starting_location.as_json,
        "amount": capacities,
        "capacity": capacities,
    }


def _get_jingle_index_for(category: ItemCategory) -> int:
    if category.is_key:
        return 2
    elif category.is_major_category and category != ItemCategory.ENERGY_TANK:
        return 1
    else:
        return 0


def _pickup_scan(pickup: PickupEntry) -> str:
    if pickup.item_category != ItemCategory.EXPANSION:
        if len(pickup.resources) > 1 and all(conditional.name is not None for conditional in pickup.resources):
            return "{}. Provides the following in order: {}".format(
                pickup.name, ", ".join(conditional.name for conditional in pickup.resources))
        else:
            return pickup.name

    return "{} that provides {}".format(
        pickup.name,
        " and ".join(
            "{} {}".format(quantity, _resource_user_friendly_name(resource))
            for resource, quantity in pickup.resources[-1].resources
        )
    )


def _create_pickup_resources_for(resources: ResourceGain):
    return [
        {
            "index": resource.index,
            "amount": quantity
        }
        for resource, quantity in resources
        if quantity > 0 and resource.resource_type == ResourceType.ITEM
    ]


def _get_single_hud_text(pickup_name: str,
                         memo_data: Dict[str, str],
                         resources: ResourceGainTuple,
                         ) -> str:
    return memo_data[pickup_name].format(**{
        _resource_user_friendly_name(resource): quantity
        for resource, quantity in resources
    })


def _get_all_hud_text(pickup: PickupEntry,
                      memo_data: Dict[str, str],
                      ) -> List[str]:
    return [
        _get_single_hud_text(conditional.name or pickup.name, memo_data, conditional.resources)
        for conditional in pickup.resources
    ]


def _calculate_hud_text(pickup: PickupEntry,
                        visual_pickup: PickupEntry,
                        model_style: PickupModelStyle,
                        memo_data: Dict[str, str],
                        ) -> List[str]:
    """
    Calculates what the hud_text for a pickup should be
    :param pickup:
    :param visual_pickup:
    :param model_style:
    :param memo_data:
    :return:
    """

    if model_style == PickupModelStyle.HIDE_ALL:
        hud_text = _get_all_hud_text(visual_pickup, memo_data)
        if len(hud_text) == len(pickup.resources):
            return hud_text
        else:
            return [hud_text[0]] * len(pickup.resources)

    else:
        return _get_all_hud_text(pickup, memo_data)


class PickupCreator:
    def __init__(self, rng: Random):
        self.rng = rng

    def create_pickup_data(self,
                           original_index: PickupIndex,
                           pickup_target: PickupTarget,
                           visual_pickup: PickupEntry,
                           model_style: PickupModelStyle,
                           scan_text: str) -> dict:
        raise NotImplementedError()

    def create_pickup(self,
                      original_index: PickupIndex,
                      pickup_target: PickupTarget,
                      visual_pickup: PickupEntry,
                      model_style: PickupModelStyle,
                      ) -> dict:
        model_pickup = pickup_target.pickup if model_style == PickupModelStyle.ALL_VISIBLE else visual_pickup

        if model_style in {PickupModelStyle.ALL_VISIBLE, PickupModelStyle.HIDE_MODEL}:
            scan_text = _pickup_scan(pickup_target.pickup)
        else:
            scan_text = visual_pickup.name

        # TODO: less improvised, really
        model_index = model_pickup.model_index
        if model_index == 22 and self.rng.randint(0, _EASTER_EGG_SHINY_MISSILE) == 0:
            # If placing a missile expansion model, replace with Dark Missile Trooper model with a 1/8192 chance
            model_index = 23

        result = {
            "pickup_index": original_index.index,
            **self.create_pickup_data(original_index, pickup_target, visual_pickup, model_style, scan_text),
            "model_index": model_index,
            "sound_index": 1 if model_pickup.item_category.is_key else 0,
            "jingle_index": _get_jingle_index_for(model_pickup.item_category),
        }
        return result


class PickupCreatorSolo(PickupCreator):
    def __init__(self, rng: Random, memo_data: Dict[str, str]):
        super().__init__(rng)
        self.memo_data = memo_data

    def create_pickup_data(self,
                           original_index: PickupIndex,
                           pickup_target: PickupTarget,
                           visual_pickup: PickupEntry,
                           model_style: PickupModelStyle,
                           scan_text: str) -> dict:
        hud_text = _calculate_hud_text(pickup_target.pickup, visual_pickup, model_style, self.memo_data)
        if hud_text == ["Energy Transfer Module acquired!"] and (
                self.rng.randint(0, _EASTER_EGG_RUN_VALIDATED_CHANCE) == 0):
            hud_text = ["Run validated!"]

        return {
            "resources": _create_pickup_resources_for(pickup_target.pickup.resources[0].resources),
            "conditional_resources": [
                {
                    "item": conditional.item.index,
                    "resources": _create_pickup_resources_for(conditional.resources),
                }
                for conditional in pickup_target.pickup.resources[1:]
            ],
            "convert": [
                {
                    "from_item": conversion.source.index,
                    "to_item": conversion.target.index,
                    "clear_source": conversion.clear_source,
                    "overwrite_target": conversion.overwrite_target,
                }
                for conversion in pickup_target.pickup.convert_resources
            ],
            "hud_text": hud_text,
            "scan": scan_text,
        }


class PickupCreatorMulti(PickupCreator):
    def __init__(self, rng: Random, memo_data: Dict[str, str], players_config: PlayersConfiguration):
        super().__init__(rng)
        self.solo_creator = PickupCreatorSolo(rng, memo_data)
        self.players_config = players_config

    def create_pickup_data(self,
                           original_index: PickupIndex,
                           pickup_target: PickupTarget,
                           visual_pickup: PickupEntry,
                           model_style: PickupModelStyle,
                           scan_text: str) -> dict:
        if pickup_target.player == self.players_config.player_index:
            result = self.solo_creator.create_pickup_data(original_index, pickup_target, visual_pickup,
                                                          model_style, scan_text)
            result["scan"] = f"Your {result['scan']}"
        else:
            other_name = self.players_config.player_names[pickup_target.player]
            result: dict = {
                "resources": [],
                "conditional_resources": [],
                "convert": [],
                "hud_text": [f"Sent {pickup_target.pickup.name} to {other_name}!"],
                "scan": f"{other_name}'s {scan_text}",
            }

        magic_resource = {
            "index": 74,
            "amount": original_index.index + 1,
        }

        result["resources"].append(magic_resource)
        for conditional in result["conditional_resources"]:
            conditional["resources"].append(magic_resource)

        return result


def _get_visual_model(original_index: int,
                      pickup_list: List[PickupTarget],
                      data_source: PickupModelDataSource,
                      ) -> PickupEntry:
    if data_source == PickupModelDataSource.ETM:
        return pickup_creator.create_visual_etm()
    elif data_source == PickupModelDataSource.RANDOM:
        return pickup_list[original_index % len(pickup_list)].pickup
    elif data_source == PickupModelDataSource.LOCATION:
        raise NotImplementedError()
    else:
        raise ValueError(f"Unknown data_source: {data_source}")


def _create_pickup_list(patches: GamePatches,
                        useless_target: PickupTarget,
                        pickup_count: int,
                        rng: Random,
                        model_style: PickupModelStyle,
                        data_source: PickupModelDataSource,
                        creator: PickupCreator,
                        ) -> list:
    """
    Creates the patcher data for all pickups in the game
    :param patches:
    :param useless_target:
    :param pickup_count:
    :param rng:
    :param model_style:
    :param data_source:
    :param creator:
    :return:
    """
    pickup_assignment = patches.pickup_assignment

    pickup_list = list(pickup_assignment.values())
    rng.shuffle(pickup_list)

    pickups = [
        creator.create_pickup(PickupIndex(i),
                              pickup_assignment.get(PickupIndex(i), useless_target),
                              _get_visual_model(i, pickup_list, data_source),
                              model_style,
                              )
        for i in range(pickup_count)
    ]

    return pickups


def _elevator_area_name(world_list: WorldList,
                        area_location: AreaLocation,
                        include_world_name: bool,
                        ) -> str:
    if area_location.area_asset_id in _CUSTOM_NAMES_FOR_ELEVATORS:
        return _CUSTOM_NAMES_FOR_ELEVATORS[area_location.area_asset_id]

    else:
        world = world_list.world_by_area_location(area_location)
        area = world.area_by_asset_id(area_location.area_asset_id)
        if include_world_name:
            return world_list.area_name(area)
        else:
            return area.name


def _pretty_name_for_elevator(world_list: WorldList,
                              original_teleporter_node: TeleporterNode,
                              connection: AreaLocation,
                              ) -> str:
    """
    Calculates the name the room that contains this elevator should have
    :param world_list:
    :param original_teleporter_node:
    :param connection:
    :return:
    """
    if original_teleporter_node.keep_name_when_vanilla:
        if original_teleporter_node.default_connection == connection:
            return world_list.nodes_to_area(original_teleporter_node).name

    return "Transport to {}".format(_elevator_area_name(world_list, connection, False))


def _create_elevators_field(patches: GamePatches, game: GameDescription) -> list:
    """
    Creates the elevator entries in the patcher file
    :param patches:
    :param game:
    :return:
    """

    world_list = game.world_list
    nodes_by_teleporter_id = _get_nodes_by_teleporter_id(world_list)
    elevator_connection = patches.elevator_connection

    if len(elevator_connection) != len(nodes_by_teleporter_id):
        raise ValueError("Invalid elevator count. Expected {}, got {}.".format(
            len(nodes_by_teleporter_id), len(elevator_connection)
        ))

    elevators = [
        {
            "instance_id": instance_id,
            "origin_location": world_list.node_to_area_location(nodes_by_teleporter_id[instance_id]).as_json,
            "target_location": connection.as_json,
            "room_name": _pretty_name_for_elevator(world_list, nodes_by_teleporter_id[instance_id], connection)
        }
        for instance_id, connection in elevator_connection.items()
    ]

    return elevators


def _get_nodes_by_teleporter_id(world_list: WorldList) -> Dict[int, TeleporterNode]:
    nodes_by_teleporter_id = {
        node.teleporter_instance_id: node

        for node in world_list.all_nodes
        if isinstance(node, TeleporterNode) and node.editable
    }
    return nodes_by_teleporter_id


def _create_translator_gates_field(gate_assignment: GateAssignment) -> list:
    """
    Creates the translator gate entries in the patcher file
    :param gate_assignment:
    :return:
    """
    return [
        {
            "gate_index": gate.index,
            "translator_index": translator.index,
        }
        for gate, translator in gate_assignment.items()
    ]


def _apply_translator_gate_patches(specific_patches: dict, elevators: LayoutElevators) -> None:
    """

    :param specific_patches:
    :param elevators:
    :return:
    """
    specific_patches["always_up_gfmc_compound"] = True
    specific_patches["always_up_torvus_temple"] = True
    specific_patches["always_up_great_temple"] = elevators != LayoutElevators.VANILLA


def _create_elevator_scan_port_patches(world_list: WorldList, elevator_connection: Dict[int, AreaLocation],
                                       ) -> Iterator[dict]:
    nodes_by_teleporter_id = _get_nodes_by_teleporter_id(world_list)

    for teleporter_id, node in nodes_by_teleporter_id.items():
        if node.scan_asset_id is None:
            continue

        target_area_name = _elevator_area_name(world_list, elevator_connection[teleporter_id], True)
        yield {
            "asset_id": node.scan_asset_id,
            "strings": [f"Access to &push;&main-color=#FF3333;{target_area_name}&pop; granted.", ""],
        }


def _logbook_title_string_patches():
    return [
        {
            "asset_id": 3271034066,
            "strings": [
                'Hints', 'Violet', 'Cobalt', 'Technology', 'Keys 1, 2, 3', 'Keys 7, 8, 9', 'Regular Hints',
                'Emerald', 'Amber', '&line-spacing=75;Flying Ing\nCache Hints', 'Keys 4, 5, 6', 'Keys 1, 2, 3',
                '&line-spacing=75;Torvus Energy\nController', 'Underground Tunnel', 'Training Chamber',
                'Catacombs', 'Gathering Hall', '&line-spacing=75;Fortress\nTransport\nAccess',
                '&line-spacing=75;Hall of Combat\nMastery', 'Main Gyro Chamber',
                '&line-spacing=75;Sanctuary\nEnergy\nController', 'Main Research', 'Watch Station',
                'Sanctuary Entrance', '&line-spacing=75;Transport to\nAgon Wastes', 'Mining Plaza',
                '&line-spacing=75;Agon Energy\nController', 'Portal Terminal', 'Mining Station B',
                'Mining Station A', 'Meeting Grounds', 'Path of Eyes', 'Path of Roots',
                '&line-spacing=75;Main Energy\nController', "A-Kul's Testament",
                '&line-spacing=75;Central\nMining\nStation', 'Main Reactor', 'Torvus Lagoon', 'Catacombs',
                'Sanctuary Entrance', "Dynamo Works", 'Storage Cavern A', 'Landing Site', 'Industrial Site',
                '&line-spacing=75;Sky Temple\nKey Hints', 'Keys 7, 8, 9', 'Keys 4, 5, 6', 'Sky Temple Key 1',
                'Sky Temple Key 2', 'Sky Temple Key 3', 'Sky Temple Key 4', 'Sky Temple Key 5',
                'Sky Temple Key 6', 'Sky Temple Key 7', 'Sky Temple Key 8', 'Sky Temple Key 9'
            ],
        }, {
            "asset_id": 2301408881,
            "strings": [
                'Research', 'Mechanisms', 'Luminoth Technology', 'Biology', 'GF Security', 'Vehicles',
                'Aether Studies', 'Aether', 'Dark Aether', 'Phazon', 'Sandgrass', 'Blueroot Tree',
                'Ing Webtrap',
                'Webling', 'U-Mos', 'Bladepod', 'Ing Storage', 'Flying Ing Cache', 'Torvus Bearerpod',
                'Agon Bearerpod', 'Ingworm Cache', 'Ingsphere Cache', 'Plantforms', 'Darklings',
                'GF Gate Mk VI',
                'GF Gate Mk VII', 'GF Lock Mk V', 'GF Defense Shield', 'Kinetic Orb Cannon', 'GF Bridge',
                "Samus's Gunship", 'GFS Tyr', 'Pirate Skiff', 'Visors', 'Weapon Systems', 'Armor',
                'Morph Ball Systems', 'Movement Systems', 'Beam Weapons', 'Scan Visor', 'Combat Visor',
                'Dark Visor',
                'Echo Visor', 'Morph Ball', 'Boost Ball', 'Spider Ball', 'Morph Ball Bomb', 'Power Bomb',
                'Dark Bomb', 'Light Bomb', 'Annihilator Bomb', 'Space Jump Boots', 'Screw Attack',
                'Gravity Boost',
                'Grapple Beam', 'Varia Suit', 'Dark Suit', 'Light Suit', 'Power Beam', 'Dark Beam',
                'Light Beam',
                'Annihilator Beam', 'Missile Launcher', 'Seeker Missile Launcher', 'Super Missile',
                'Sonic Boom',
                'Darkburst', 'Sunburst', 'Charge Beam', 'Missile Systems', 'Charge Combos', 'Morph Balls',
                'Bomb Systems', 'Miscellaneous', 'Dark Temple Keys', 'Bloatsac', 'Luminoth Technology',
                'Light Beacons', 'Light Crystals', 'Lift Crystals', 'Utility Crystals', 'Light Crystal',
                'Energized Crystal', 'Nullified Crystal', 'Super Crystal', 'Light Beacon', 'Energized Beacon',
                'Nullified Beacon', 'Super Beacon', 'Inactive Beacon', 'Dark Lift Crystal',
                'Light Lift Crystal',
                'Liftvine Crystal', 'Torvus Hanging Pod', 'Sentinel Crystal', 'Dark Sentinel Crystal',
                'Systems',
                'Bomb Slot', 'Spinner', 'Grapple Point', 'Spider Ball Track', 'Energy Tank',
                'Beam Ammo Expansion',
                'Missile Expansion', 'Dark Agon Keys', 'Dark Torvus Keys', 'Ing Hive Keys', 'Sky Temple Keys',
                'Temple Grounds', 'Sanctuary Fortress', 'Torvus Bog', 'Agon Wastes', 'Dark Agon Temple Key 1',
                'Dark Agon Temple Key 2', 'Dark Agon Temple Key 3', 'Dark Torvus Temple Key 1',
                'Dark Torvus Temple Key 2', 'Dark Torvus Temple Key 3', 'Ing Hive Temple Key 1',
                'Ing Hive Temple Key 2', 'Ing Hive Temple Key 3', 'Sky Temple Key 1', 'Sky Temple Key 2',
                'Sky Temple Key 3', 'Sky Temple Key 4', 'Sky Temple Key 5', 'Sky Temple Key 6',
                'Sky Temple Key 7',
                'Sky Temple Key 8', 'Sky Temple Key 9', 'Suit Expansions', 'Charge Combo', 'Ingclaw',
                'Dormant Ingclaw', 'Power Bomb Expansion', 'Energy Transfer Module', 'Cocoons',
                'Splinter Cocoon',
                'War Wasp Hive', 'Metroid Cocoon', 'Dark Aether', 'Aether', 'Dark Portal', 'Light Portal',
                'Energy Controller', 'Wall Jump Surface',
            ]
        },
    ]


def _create_string_patches(hint_config: HintConfiguration,
                           game: GameDescription,
                           all_patches: Dict[int, GamePatches],
                           players_config: PlayersConfiguration,
                           rng: Random,
                           ) -> list:
    """

    :param hint_config:
    :param game:
    :param patches:
    :return:
    """
    patches = all_patches[players_config.player_index]
    string_patches = []

    # Location Hints
    string_patches.extend(
        item_hints.create_hints(all_patches, players_config, game.world_list, rng)
    )

    # Sky Temple Keys
    stk_mode = hint_config.sky_temple_keys
    if stk_mode == SkyTempleKeyHintMode.DISABLED:
        string_patches.extend(sky_temple_key_hint.hide_hints())
    else:
        string_patches.extend(sky_temple_key_hint.create_hints(all_patches, players_config, game.world_list,
                                                               stk_mode == SkyTempleKeyHintMode.HIDE_AREA))

    # Elevator Scans
    string_patches.extend(_create_elevator_scan_port_patches(game.world_list, patches.elevator_connection))

    string_patches.extend(_logbook_title_string_patches())

    return string_patches


def additional_starting_items(layout_configuration: EchoesConfiguration,
                              resource_database: ResourceDatabase,
                              starting_items: CurrentResources) -> List[str]:
    initial_items = pool_creator.calculate_pool_results(layout_configuration, resource_database)[2]

    return [
        "{}{}".format("{} ".format(quantity) if quantity > 1 else "", _resource_user_friendly_name(item))
        for item, quantity in starting_items.items()
        if 0 < quantity != initial_items.get(item, 0)
    ]


def _create_starting_popup(layout_configuration: EchoesConfiguration,
                           resource_database: ResourceDatabase,
                           starting_items: CurrentResources) -> list:
    extra_items = additional_starting_items(layout_configuration, resource_database, starting_items)
    if extra_items:
        return [
            "Extra starting items:",
            ", ".join(extra_items)
        ]
    else:
        return []


class _SimplifiedMemo(dict):
    def __missing__(self, key):
        return "{} acquired!".format(key)


def _simplified_memo_data() -> Dict[str, str]:
    result = _SimplifiedMemo()
    result["Temporary Power Bombs"] = "Power Bomb Expansion acquired, but the main Power Bomb is required to use it."
    result["Temporary Missile"] = "Missile Expansion acquired, but the Missile Launcher is required to use it."
    return result


def create_patcher_file(description: LayoutDescription,
                        players_config: PlayersConfiguration,
                        cosmetic_patches: CosmeticPatches,
                        ) -> dict:
    """

    :param description:
    :param players_config:
    :param cosmetic_patches:
    :return:
    """
    preset = description.permalink.get_preset(players_config.player_index)
    configuration = preset.configuration
    patches = description.all_patches[players_config.player_index]
    rng = Random(description.permalink.seed_number)

    game = data_reader.decode_data(configuration.game_data)
    pickup_count = game.world_list.num_pickup_nodes
    useless_target = PickupTarget(pickup_creator.create_useless_pickup(game.resource_database),
                                  players_config.player_index)

    result = {}
    _add_header_data_to_result(description, result)

    result["menu_mod"] = configuration.menu_mod
    result["user_preferences"] = cosmetic_patches.user_preferences.as_json
    result["default_items"] = {
        "visor": configuration.major_items_configuration.default_items[ItemCategory.VISOR].name,
        "beam": configuration.major_items_configuration.default_items[ItemCategory.BEAM].name,
    }

    # Add Spawn Point
    result["spawn_point"] = _create_spawn_point_field(patches, game.resource_database)

    result["starting_popup"] = _create_starting_popup(configuration, game.resource_database, patches.starting_items)

    # Add the pickups
    if cosmetic_patches.disable_hud_popup:
        memo_data = _simplified_memo_data()
    else:
        memo_data = default_prime2_memo_data()

    if description.permalink.player_count == 1:
        creator = PickupCreatorSolo(rng, memo_data)
    else:
        creator = PickupCreatorMulti(rng, memo_data, players_config)

    result["pickups"] = _create_pickup_list(patches,
                                            useless_target, pickup_count,
                                            rng,
                                            configuration.pickup_model_style,
                                            configuration.pickup_model_data_source,
                                            creator=creator,
                                            )

    # Add the elevators
    result["elevators"] = _create_elevators_field(patches, game)

    # Add translators
    result["translator_gates"] = _create_translator_gates_field(patches.translator_gates)

    # Scan hints
    result["string_patches"] = _create_string_patches(configuration.hints, game, description.all_patches, players_config, rng)

    # TODO: if we're starting at ship, needs to collect 9 sky temple keys and want item loss,
    # we should disable hive_chamber_b_post_state
    result["specific_patches"] = {
        "hive_chamber_b_post_state": True,
        "intro_in_post_state": True,
        "warp_to_start": configuration.warp_to_start,
        "speed_up_credits": cosmetic_patches.speed_up_credits,
        "disable_hud_popup": cosmetic_patches.disable_hud_popup,
        "pickup_map_icons": cosmetic_patches.pickup_markers,
        "full_map_at_start": cosmetic_patches.open_map,
        "dark_world_varia_suit_damage": configuration.varia_suit_damage,
        "dark_world_dark_suit_damage": configuration.dark_suit_damage,
    }

    result["logbook_patches"] = [
        {"asset_id": 25, "connections": [81, 166, 195], },
        {"asset_id": 38, "connections": [4, 33, 120, 251, 364], },
        {"asset_id": 60, "connections": [38, 74, 154, 196], },
        {"asset_id": 74, "connections": [59, 75, 82, 102, 260], },
        {"asset_id": 81, "connections": [148, 151, 156], },
        {"asset_id": 119, "connections": [60, 254, 326], },
        {"asset_id": 124, "connections": [35, 152, 355], },
        {"asset_id": 129, "connections": [29, 118, 367], },
        {"asset_id": 154, "connections": [169, 200, 228, 243, 312, 342], },
        {"asset_id": 166, "connections": [45, 303, 317], },
        {"asset_id": 194, "connections": [1, 6], },
        {"asset_id": 195, "connections": [159, 221, 231], },
        {"asset_id": 196, "connections": [17, 19, 23, 162, 183, 379], },
        {"asset_id": 233, "connections": [58, 191, 373], },
        {"asset_id": 241, "connections": [223, 284], },
        {"asset_id": 254, "connections": [129, 233, 319], },
        {"asset_id": 318, "connections": [119, 216, 277, 343], },
        {"asset_id": 319, "connections": [52, 289, 329], },
        {"asset_id": 326, "connections": [124, 194, 241, 327], },
        {"asset_id": 327, "connections": [46, 275], },
    ]

    _apply_translator_gate_patches(result["specific_patches"], configuration.elevators)

    return result


def _add_header_data_to_result(description: LayoutDescription, result: dict) -> None:
    result["permalink"] = "-permalink-"
    result["seed_hash"] = f"- {description.shareable_word_hash} ({description.shareable_hash})"
    result["randovania_version"] = randovania.VERSION
