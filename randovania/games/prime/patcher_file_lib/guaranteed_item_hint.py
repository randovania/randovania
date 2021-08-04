from typing import List, Dict, Tuple, Optional

from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resources import resource_info
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.prime.patcher_file_lib import hint_lib
from randovania.interface_common.players_configuration import PlayersConfiguration


def find_locations_that_gives_items(
        target_items: List[ItemResourceInfo],
        all_patches: Dict[int, GamePatches],
        player: int,
) -> Dict[ItemResourceInfo, List[Tuple[int, PickupIndex]]]:
    result = {item: [] for item in target_items}

    for other_player, patches in all_patches.items():
        for pickup_index, target in patches.pickup_assignment.items():
            if target.player != player:
                continue

            # TODO: iterate over all tiers of progression
            resources = resource_info.convert_resource_gain_to_current_resources(target.pickup.resource_gain({}))

            for resource, quantity in resources.items():
                if quantity > 0 and resource in result:
                    result[resource].append((other_player, pickup_index))

    return result


def hint_text_if_items_are_starting(
        target_items: List[ItemResourceInfo],
        all_patches: Dict[int, GamePatches],
        player: int,
        resource_color: hint_lib.TextColor,
) -> Dict[ItemResourceInfo, str]:
    result = {}

    for resource, quantity in all_patches[player].starting_items.items():
        if quantity > 0 and resource in target_items:
            result[resource] = "{} has no need to be located.".format(
                hint_lib.color_text(resource_color, resource.long_name))

    return result


def create_guaranteed_hints_for_resources(
        all_patches: Dict[int, GamePatches],
        players_config: PlayersConfiguration,
        area_namers: Dict[int, hint_lib.AreaNamer],
        hide_area: bool,
        items: List[ItemResourceInfo],
        resource_color: hint_lib.TextColor,
        location_color: hint_lib.TextColor,
) -> Dict[ItemResourceInfo, str]:
    """
    Creates a hint for where each of the given resources for the given player can be found, across all players.
    If the player starts with the resource, indicate such. Errors if any resource can't be found.
    Intended for Sky Temple Key/Artifacts hints.

    :param all_patches:
    :param players_config:
    :param area_namers: Area namer for all players in the LayoutDescription
    :param hide_area: Should the area of the location be hidden?
    :param items: The item resources to hint
    :param resource_color: The color to use for resource names.
    :param location_color: The color to use for location names.
    :return:
    """
    resulting_hints = hint_text_if_items_are_starting(items, all_patches, players_config.player_index, resource_color)
    locations_for_items = find_locations_that_gives_items(items, all_patches, players_config.player_index)

    used_locations = set()
    for resource, locations in locations_for_items.items():
        if resource in resulting_hints:
            continue

        location: Optional[Tuple[int, PickupIndex]] = None
        for option in locations:
            if option not in used_locations:
                location = option
                break

        if location is not None:
            used_locations.add(location)

            if players_config.is_multiworld:
                determiner = hint_lib.player_determiner(players_config, location[0])
            else:
                determiner = hint_lib.Determiner("", False)

            resulting_hints[resource] = "{} is located in {}{}.".format(
                hint_lib.color_text(resource_color, resource.long_name),
                determiner,
                area_namers[location[0]].location_name(location[1], hide_area, color=location_color),
            )

    if len(resulting_hints) != len(items):
        raise ValueError(
            "Expected to find {} between pickup placement and starting items, found {}".format(
                len(items),
                len(resulting_hints)
            ))

    return resulting_hints
