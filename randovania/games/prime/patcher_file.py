from typing import Dict

import randovania
from randovania.game_description import data_reader
from randovania.game_description.area_location import AreaLocation
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.node import TeleporterNode
from randovania.game_description.resource_type import ResourceType
from randovania.game_description.resources import SimpleResourceInfo, ResourceGain, ResourceDatabase, PickupIndex, \
    PickupEntry
from randovania.game_description.world_list import WorldList
from randovania.interface_common.cosmetic_patches import CosmeticPatches
from randovania.layout.layout_configuration import LayoutConfiguration
from randovania.layout.layout_description import LayoutDescription
from randovania.layout.starting_location import StartingLocationConfiguration
from randovania.layout.starting_resources import StartingResourcesConfiguration
from randovania.resolver.item_pool.pickup_creator import create_useless_pickup

_TOTAL_PICKUP_COUNT = 119
_CUSTOM_NAMES_FOR_ELEVATORS = {
    1660916974: "Grounds from Agon",
    2889020216: "Grounds from Torvus",
    3455543403: "Grounds from Sanctuary",
    1473133138: "Agon Entrance",
    2806956034: "Agon from Torvus",
    3331021649: "Agon from Sanctuary",
    1868895730: "Torvus Entrance",
    3479543630: "Torvus from Agon",
    3205424168: "Torvus Sanctuary",
    3528156989: "Sanctuary Entrance",
    900285955: "Sanctuary from Agon",
    3145160350: "Sanctuary from Torvus",
}


def _add_items_in_resource_gain_to_dict(gain: ResourceGain,
                                        target: Dict[SimpleResourceInfo, int],
                                        ):
    """
    :param gain:
    :param target:
    :return:
    """
    for resource, quantity in gain:
        if resource.resource_type == ResourceType.ITEM:
            target[resource] = target.get(resource, 0) + quantity


def _create_spawn_point_field(patches: GamePatches,
                              resource_database: ResourceDatabase,
                              ) -> dict:
    # TODO: we don't need the aux function and this conversion to dict
    # A GamePatches already ensures there's no copies to the extra_initial_items
    item_quantities: Dict[SimpleResourceInfo, int] = {}
    _add_items_in_resource_gain_to_dict(patches.extra_initial_items,
                                        item_quantities)

    capacities = [
        {
            "index": item.index,
            "amount": item_quantities.get(item, 0),
        }
        for item in resource_database.item
    ]

    return {
        "location": patches.starting_location.as_json,
        "amount": capacities,
        "capacity": capacities,
    }


_item_category_to_jingle_index = {
    "major": 1,
    "translator": 1,
    "temple_key": 2,
    "sky_temple_key": 2
}


def _pickup_scan(pickup: PickupEntry) -> str:
    if pickup.item_category != "expansion":
        return pickup.name

    return "{0} that provides {1}".format(
        pickup.name,
        ", ".join(
            "{} {}".format(quantity, resource.long_name)
            for resource, quantity in pickup.resources
        )
    )


def _create_pickup(original_index: PickupIndex, pickup: PickupEntry) -> dict:
    # TODO: we can use the resource name here to avoid saying "Progressive Suit" acquired
    # But using resource name also breaks things like vanilla beam ammo expansion
    # And 'Missile Expansion' shows up as 'Missile'.
    hud_text = [
        "{} acquired!".format(pickup.name),
        # "{} acquired!".format(pickup.resources[0][0].long_name),
    ]
    conditional_resources = []

    for conditional in pickup.conditional_resources:
        hud_text.append("{} acquired!".format(pickup.name))
        # hud_text.append("{} acquired!".format(conditional.resources[0][0].long_name))
        conditional_resources.append({
            "item": conditional.item.index,
            "resources": [
                {
                    "index": resource.index,
                    "amount": quantity
                }
                for resource, quantity in conditional.resources
                if quantity > 0 and resource.resource_type == ResourceType.ITEM
            ]
        })

    result = {
        "pickup_index": original_index.index,
        "model_index": pickup.model_index,
        "scan": _pickup_scan(pickup),
        "hud_text": hud_text,
        "sound_index": 1 if pickup.item_category in {"temple_key", "sky_temple_key"} else 0,
        "jingle_index": _item_category_to_jingle_index.get(pickup.item_category, 0),
        "resources": [
            {
                "index": resource.index,
                "amount": quantity
            }
            for resource, quantity in pickup.resources
            if quantity > 0 and resource.resource_type == ResourceType.ITEM
        ],
        "conditional_resources": conditional_resources,
    }
    return result


def _create_pickup_list(patches: GamePatches,
                        useless_pickup: PickupEntry,
                        pickup_count: int,
                        ) -> list:
    pickup_assignment = patches.pickup_assignment

    pickups = [
        _create_pickup(PickupIndex(i), pickup_assignment.get(PickupIndex(i), useless_pickup))
        for i in range(pickup_count)
    ]

    return pickups


def _pretty_name_for_elevator(world_list: WorldList, connection: AreaLocation) -> str:
    if connection.area_asset_id in _CUSTOM_NAMES_FOR_ELEVATORS:
        return _CUSTOM_NAMES_FOR_ELEVATORS[connection.area_asset_id]

    world = world_list.world_by_area_location(connection)
    area = world.area_by_asset_id(connection.area_asset_id)
    return "{0.name} - {1.name}".format(world, area)


def _create_elevators_field(patches: GamePatches, world_list: WorldList) -> list:
    """
    Creates the elevator entries in the patcher file
    :param patches:
    :param world_list:
    :return:
    """

    nodes_by_teleporter_id = {
        node.teleporter_instance_id: node
        for node in world_list.all_nodes
        if isinstance(node, TeleporterNode)
    }

    elevators = [
        {
            "instance_id": instance_id,
            "origin_location": world_list.node_to_area_location(nodes_by_teleporter_id[instance_id]).as_json,
            "target_location": connection.as_json,
            "room_name": "Transport to {}".format(_pretty_name_for_elevator(world_list, connection))
        }
        for instance_id, connection in patches.elevator_connection.items()
    ]

    return elevators


def create_patcher_file(description: LayoutDescription,
                        cosmetic_patches: CosmeticPatches) -> dict:
    patcher_config = description.permalink.patcher_configuration
    layout = description.permalink.layout_configuration
    patches = description.patches
    game = data_reader.decode_data(layout.game_data, add_self_as_requirement_to_resources=False)
    useless_pickup = create_useless_pickup(game.resource_database)

    result = {}
    _add_header_data_to_result(description, result)

    # Add Spawn Point
    result["spawn_point"] = _create_spawn_point_field(patches, game.resource_database)

    # Add the pickups
    result["pickups"] = _create_pickup_list(patches, useless_pickup, _TOTAL_PICKUP_COUNT)

    # Add the elevators
    result["elevators"] = _create_elevators_field(patches, game.world_list)

    # TODO: if we're starting at ship, needs to collect 8 sky temple keys and want item loss,
    # we should disable hive_chamber_b_post_state
    result["specific_patches"] = {
        "hive_chamber_b_post_state": True,
        "intro_in_post_state": True,
        "warp_to_start": patcher_config.warp_to_start,
        "speed_up_credits": cosmetic_patches.speed_up_credits,
        "disable_hud_popup": cosmetic_patches.disable_hud_popup,
    }

    return result


def _add_header_data_to_result(description: LayoutDescription, result: dict) -> None:
    # FIXME: these shouldn't be tuples
    result["permalink"] = description.permalink.as_str,
    result["seed_hash"] = description.shareable_hash,
    result["randovania_version"] = randovania.VERSION,


def is_vanilla_starting_location(configuration: LayoutConfiguration) -> bool:
    loc_config = configuration.starting_location.configuration
    resource_config = configuration.starting_resources.configuration
    return (loc_config == StartingLocationConfiguration.SHIP and
            resource_config == StartingResourcesConfiguration.VANILLA_ITEM_LOSS_ENABLED)
