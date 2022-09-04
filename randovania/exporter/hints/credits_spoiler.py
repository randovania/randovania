import collections
import math
from typing import NamedTuple

from randovania.exporter.hints.hint_namer import HintNamer, PickupLocation
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.layout.base.major_items_configuration import MajorItemsConfiguration


class OwnedPickupLocation(NamedTuple):
    player_name: str | None
    location: PickupLocation

    def export(self, namer: HintNamer) -> str:
        hint = namer.format_location(self.location, with_world=True, with_area=True, with_color=False)
        if self.player_name is not None:
            hint = f"{namer.format_player(self.player_name, with_color=True)}'s {hint}"
        return hint


def get_locations_for_major_pickups_and_keys(
        all_patches: dict[int, GamePatches],
        players_config: PlayersConfiguration,
) -> dict[PickupEntry, list[OwnedPickupLocation]]:
    results: dict[PickupEntry, list[OwnedPickupLocation]] = collections.defaultdict(list)

    for player_index, patches in all_patches.items():
        for pickup_index, target in patches.pickup_assignment.items():
            if target.player != players_config.player_index:
                continue

            item_category = target.pickup.item_category
            if item_category.is_major or item_category.is_key:
                player_name = None
                if players_config.is_multiworld:
                    player_name = players_config.player_names[player_index]

                results[target.pickup].append(
                    OwnedPickupLocation(player_name, PickupLocation(patches.configuration.game, pickup_index))
                )

    return results


def generic_credits(
        major_items_configuration: MajorItemsConfiguration,
        all_patches: dict[int, GamePatches],
        players_config: PlayersConfiguration,
        namer: HintNamer,
        pickup_name_format: str = "{}",
) -> dict[str, str]:
    major_name_order = {
        pickup.name: index
        for index, pickup in enumerate(major_items_configuration.items_state.keys())
    }

    def sort_pickup(p: PickupEntry):
        return major_name_order.get(p.name, math.inf), p.name

    details = get_locations_for_major_pickups_and_keys(all_patches, players_config)
    major_pickups_spoiler = {
        pickup: [
            entry.export(namer) for entry in entries
        ]
        for pickup, entries in details.items()
    }

    return {
        pickup_name_format.format(pickup.name):
        "\n".join(major_pickups_spoiler[pickup]) or "Nowhere"
        for pickup in sorted(major_pickups_spoiler.keys(), key=sort_pickup)
    }


def prime_trilogy_credits(
        major_items_configuration: MajorItemsConfiguration,
        all_patches: dict[int, GamePatches],
        players_config: PlayersConfiguration,
        namer: HintNamer,
        title: str,
        pickup_name_format: str,
) -> str:
    credit_items = generic_credits(
        major_items_configuration,
        all_patches,
        players_config,
        namer,
        pickup_name_format
    )

    credits_lines = [f"{pickup}\n{location}" for pickup, location in credit_items.items()]

    credits_lines.insert(0, title)
    return "\n\n".join(credits_lines)
