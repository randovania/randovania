from typing import List, Dict, Tuple, Optional

from randovania.exporter.hints.hint_namer import HintNamer, PickupLocation
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resources import resource_info
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.resource_info import ResourceCollection
from randovania.interface_common.players_configuration import PlayersConfiguration


def find_locations_that_gives_items(
        target_items: List[ItemResourceInfo],
        all_patches: Dict[int, GamePatches],
        player: int,
) -> dict[ItemResourceInfo, list[tuple[int, PickupLocation]]]:
    result: dict[ItemResourceInfo, list[tuple[int, PickupLocation]]] = {item: [] for item in target_items}

    for other_player, patches in all_patches.items():
        for pickup_index, target in patches.pickup_assignment.items():
            if target.player != player:
                continue

            # TODO: iterate over all tiers of progression

            resources = ResourceCollection.from_resource_gain(target.pickup.resource_gain(ResourceCollection()))
            for resource, quantity in resources.as_resource_gain():
                if quantity > 0 and resource in result:
                    result[resource].append((other_player, PickupLocation(patches.configuration.game, pickup_index)))

    return result


def hint_text_if_items_are_starting(
        target_items: list[ItemResourceInfo],
        all_patches: dict[int, GamePatches],
        player: int,
        namer: HintNamer,
        with_color: bool,
) -> dict[ItemResourceInfo, str]:
    result = {}

    for resource, quantity in all_patches[player].starting_items.as_resource_gain():
        if quantity > 0 and resource in target_items:
            result[resource] = namer.format_resource_is_starting(resource, with_color)

    return result


def create_guaranteed_hints_for_resources(all_patches: Dict[int, GamePatches], players_config: PlayersConfiguration,
                                          namer: HintNamer, hide_area: bool, items: List[ItemResourceInfo],
                                          with_color: bool,
                                          ) -> dict[ItemResourceInfo, str]:
    """
    Creates a hint for where each of the given resources for the given player can be found, across all players.
    If the player starts with the resource, indicate such. Errors if any resource can't be found.
    Intended for Sky Temple Key/Artifacts hints.

    :param all_patches:
    :param players_config:
    :param namer:
    :param hide_area: Should the area of the location be hidden?
    :param items: The item resources to hint
    :param with_color
    :return:
    """
    resulting_hints = hint_text_if_items_are_starting(items, all_patches, players_config.player_index, namer,
                                                      with_color)
    locations_for_items = find_locations_that_gives_items(items, all_patches, players_config.player_index)

    used_locations = set()
    for resource, locations in locations_for_items.items():
        if resource in resulting_hints:
            continue

        location: Optional[Tuple[int, PickupLocation]] = None
        for option in locations:
            if option not in used_locations:
                location = option
                break

        if location is not None:
            used_locations.add(location)

            player_name = None
            if players_config.is_multiworld:
                player_name = players_config.player_names[location[0]]

            resulting_hints[resource] = namer.format_guaranteed_resource(
                resource,
                player_name,
                location[1],
                hide_area,
                with_color,
            )

    if len(resulting_hints) != len(items):
        raise ValueError(
            "Expected to find {} between pickup placement and starting items, found {}".format(
                len(items),
                len(resulting_hints)
            ))

    return resulting_hints
