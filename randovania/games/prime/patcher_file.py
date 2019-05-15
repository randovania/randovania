from random import Random
from typing import Dict, List, Optional

import randovania
from randovania.game_description import data_reader
from randovania.game_description.area_location import AreaLocation
from randovania.game_description.assignment import GateAssignment
from randovania.game_description.default_database import default_prime2_memo_data
from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.node import TeleporterNode
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
from randovania.layout.hint_configuration import HintConfiguration, SkyTempleKeyHintMode
from randovania.layout.layout_configuration import LayoutConfiguration
from randovania.layout.layout_description import LayoutDescription
from randovania.layout.patcher_configuration import PickupModelStyle, PickupModelDataSource
from randovania.layout.translator_configuration import TranslatorConfiguration

_TOTAL_PICKUP_COUNT = 119
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

_TELEPORTERS_THAT_KEEP_NAME_WHEN_VANILLA = {
    136970379,  # Sky Temple Gateway
    589949,  # Sky Temple Energy Controller
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
            return "{}: Provides the following in order: {}".format(
                pickup.name, ", ".join(conditional.name for conditional in pickup.resources))
        else:
            return pickup.name

    return "{0} that provides {1}".format(
        pickup.name,
        ", ".join(
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
                         memo_data: Optional[Dict[str, str]],
                         resources: ResourceGainTuple,
                         ) -> str:
    if memo_data is None:
        return "{} acquired!".format(pickup_name)
    else:
        return memo_data[pickup_name].format(**{
            _resource_user_friendly_name(resource): quantity
            for resource, quantity in resources
        })


def _get_all_hud_text(pickup: PickupEntry,
                      memo_data: Optional[Dict[str, str]],
                      ) -> List[str]:
    return [
        _get_single_hud_text(conditional.name or pickup.name, memo_data, conditional.resources)
        for conditional in pickup.resources
    ]


def _calculate_hud_text(pickup: PickupEntry,
                        visual_pickup: PickupEntry,
                        model_style: PickupModelStyle,
                        memo_data: Optional[Dict[str, str]],
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


def _create_pickup(original_index: PickupIndex,
                   pickup: PickupEntry,
                   visual_pickup: PickupEntry,
                   model_style: PickupModelStyle,
                   memo_data: Optional[Dict[str, str]],
                   ) -> dict:
    model_pickup = pickup if model_style == PickupModelStyle.ALL_VISIBLE else visual_pickup

    result = {
        "pickup_index": original_index.index,
        "resources": _create_pickup_resources_for(pickup.resources[0].resources),
        "conditional_resources": [
            {
                "item": conditional.item.index,
                "resources": _create_pickup_resources_for(conditional.resources),
            }
            for conditional in pickup.resources[1:]
        ],
        "convert": [
            {
                "from_item": conversion.source.index,
                "to_item": conversion.target.index,
                "clear_source": conversion.clear_source,
                "overwrite_target": conversion.overwrite_target,
            }
            for conversion in pickup.convert_resources
        ],

        "hud_text": _calculate_hud_text(pickup, visual_pickup, model_style, memo_data),

        "scan": _pickup_scan(pickup) if model_style in {PickupModelStyle.ALL_VISIBLE,
                                                        PickupModelStyle.HIDE_MODEL} else visual_pickup.name,
        "model_index": model_pickup.model_index,
        "sound_index": 1 if model_pickup.item_category.is_key else 0,
        "jingle_index": _get_jingle_index_for(model_pickup.item_category),
    }
    return result


def _get_visual_model(original_index: int,
                      pickup_list: List[PickupEntry],
                      data_source: PickupModelDataSource,
                      ) -> PickupEntry:
    if data_source == PickupModelDataSource.ETM:
        return pickup_creator.create_visual_etm()
    elif data_source == PickupModelDataSource.RANDOM:
        return pickup_list[original_index % len(pickup_list)]
    elif data_source == PickupModelDataSource.LOCATION:
        raise NotImplementedError()
    else:
        raise ValueError(f"Unknown data_source: {data_source}")


def _create_pickup_list(patches: GamePatches,
                        useless_pickup: PickupEntry,
                        pickup_count: int,
                        rng: Random,
                        model_style: PickupModelStyle,
                        data_source: PickupModelDataSource,
                        memo_data: Optional[Dict[str, str]],
                        ) -> list:
    """
    Creates the patcher data for all pickups in the game
    :param patches:
    :param useless_pickup:
    :param pickup_count:
    :param rng:
    :param model_style:
    :param data_source:
    :return:
    """
    pickup_assignment = patches.pickup_assignment

    pickup_list = list(pickup_assignment.values())
    rng.shuffle(pickup_list)

    pickups = [
        _create_pickup(PickupIndex(i),
                       pickup_assignment.get(PickupIndex(i), useless_pickup),
                       _get_visual_model(i, pickup_list, data_source),
                       model_style,
                       memo_data,
                       )
        for i in range(pickup_count)
    ]

    return pickups


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
    if original_teleporter_node.teleporter_instance_id in _TELEPORTERS_THAT_KEEP_NAME_WHEN_VANILLA:
        if original_teleporter_node.default_connection == connection:
            return world_list.nodes_to_area(original_teleporter_node).name

    if connection.area_asset_id in _CUSTOM_NAMES_FOR_ELEVATORS:
        target_area_name = _CUSTOM_NAMES_FOR_ELEVATORS[connection.area_asset_id]

    else:
        world = world_list.world_by_area_location(connection)
        area = world.area_by_asset_id(connection.area_asset_id)
        target_area_name = area.name

    return "Transport to {}".format(target_area_name)


def _create_elevators_field(patches: GamePatches, game: GameDescription) -> list:
    """
    Creates the elevator entries in the patcher file
    :param patches:
    :param game:
    :return:
    """

    world_list = game.world_list
    nodes_by_teleporter_id = {
        node.teleporter_instance_id: node
        for node in game.all_editable_teleporter_nodes()
    }

    if len(patches.elevator_connection) != len(nodes_by_teleporter_id):
        raise ValueError("Invalid elevator count. Expected {}, got {}.".format(
            len(nodes_by_teleporter_id), len(patches.elevator_connection)
        ))

    elevators = [
        {
            "instance_id": instance_id,
            "origin_location": world_list.node_to_area_location(nodes_by_teleporter_id[instance_id]).as_json,
            "target_location": connection.as_json,
            "room_name": _pretty_name_for_elevator(world_list, nodes_by_teleporter_id[instance_id], connection)
        }
        for instance_id, connection in patches.elevator_connection.items()
    ]

    return elevators


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


def _apply_translator_gate_patches(specific_patches: dict, translator_gates: TranslatorConfiguration) -> None:
    """

    :param specific_patches:
    :param translator_gates:
    :return:
    """
    specific_patches["always_up_gfmc_compound"] = translator_gates.fixed_gfmc_compound
    specific_patches["always_up_torvus_temple"] = translator_gates.fixed_torvus_temple
    specific_patches["always_up_great_temple"] = translator_gates.fixed_great_temple


def _create_string_patches(hint_config: HintConfiguration,
                           game: GameDescription,
                           patches: GamePatches,
                           rng: Random,
                           ) -> list:
    """

    :param hint_config:
    :param game:
    :param patches:
    :return:
    """
    string_patches = []

    # Location Hints
    string_patches.extend(
        item_hints.create_hints(patches, game.world_list, rng)
    )

    # Sky Temple Keys
    stk_mode = hint_config.sky_temple_keys
    if stk_mode == SkyTempleKeyHintMode.DISABLED:
        string_patches.extend(sky_temple_key_hint.hide_hints())
    else:
        string_patches.extend(sky_temple_key_hint.create_hints(patches, game.world_list,
                                                               stk_mode == SkyTempleKeyHintMode.HIDE_AREA))

    return string_patches


def _create_starting_popup(layout_configuration: LayoutConfiguration,
                           resource_database: ResourceDatabase,
                           starting_items: CurrentResources) -> list:

    initial_items = pool_creator.calculate_pool_results(layout_configuration, resource_database)[2]

    extra_items = [
        "{}{}".format("{} ".format(quantity) if quantity > 1 else "", _resource_user_friendly_name(item))
        for item, quantity in starting_items.items()
        if 0 < quantity != initial_items.get(item, 0)
    ]

    if extra_items:
        return [
            "Extra starting items:",
            ", ".join(extra_items)
        ]
    else:
        return []


def create_patcher_file(description: LayoutDescription,
                        cosmetic_patches: CosmeticPatches,
                        ) -> dict:
    """

    :param description:
    :param cosmetic_patches:
    :return:
    """
    patcher_config = description.permalink.patcher_configuration
    layout = description.permalink.layout_configuration
    patches = description.patches
    rng = Random(description.permalink.as_str)

    game = data_reader.decode_data(layout.game_data)
    useless_pickup = pickup_creator.create_useless_pickup(game.resource_database)

    result = {}
    _add_header_data_to_result(description, result)

    # Add Spawn Point
    result["spawn_point"] = _create_spawn_point_field(patches, game.resource_database)

    result["starting_popup"] = _create_starting_popup(layout, game.resource_database, patches.starting_items)

    # Add the pickups
    if cosmetic_patches.disable_hud_popup:
        memo_data = None
    else:
        memo_data = default_prime2_memo_data()

    result["pickups"] = _create_pickup_list(patches, useless_pickup, _TOTAL_PICKUP_COUNT,
                                            rng,
                                            patcher_config.pickup_model_style,
                                            patcher_config.pickup_model_data_source,
                                            memo_data,
                                            )

    # Add the elevators
    result["elevators"] = _create_elevators_field(patches, game)

    # Add translators
    result["translator_gates"] = _create_translator_gates_field(patches.translator_gates)

    # Scan hints
    result["string_patches"] = _create_string_patches(layout.hints, game, patches, rng)

    # TODO: if we're starting at ship, needs to collect 8 sky temple keys and want item loss,
    # we should disable hive_chamber_b_post_state
    result["specific_patches"] = {
        "hive_chamber_b_post_state": True,
        "intro_in_post_state": True,
        "warp_to_start": patcher_config.warp_to_start,
        "speed_up_credits": cosmetic_patches.speed_up_credits,
        "disable_hud_popup": cosmetic_patches.disable_hud_popup,
        "pickup_map_icons": cosmetic_patches.pickup_markers,
        "full_map_at_start": cosmetic_patches.open_map,
        "dark_world_varia_suit_damage": patcher_config.varia_suit_damage,
        "dark_world_dark_suit_damage": patcher_config.dark_suit_damage,
    }

    _apply_translator_gate_patches(result["specific_patches"], layout.translator_configuration)

    return result


def _add_header_data_to_result(description: LayoutDescription, result: dict) -> None:
    result["permalink"] = description.permalink.as_str
    result["seed_hash"] = description.shareable_hash
    result["randovania_version"] = randovania.VERSION
