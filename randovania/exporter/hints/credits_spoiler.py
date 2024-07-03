from __future__ import annotations

import collections
import math
from typing import TYPE_CHECKING, NamedTuple

from randovania.exporter.hints.hint_namer import HintNamer, PickupLocation
from randovania.generator.pickup_pool import pool_creator

if TYPE_CHECKING:
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.pickup.pickup_entry import PickupEntry
    from randovania.interface_common.players_configuration import PlayersConfiguration
    from randovania.layout.base.standard_pickup_configuration import StandardPickupConfiguration


class OwnedPickupLocation(NamedTuple):
    player_name: str | None
    location: PickupLocation

    def export(self, namer: HintNamer, use_player_color: bool = True) -> str:
        hint = namer.format_location(self.location, with_region=True, with_area=True, with_color=False)
        if self.player_name is not None:
            hint = f"{namer.format_player(self.player_name, with_color=use_player_color)}'s {hint}"
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

            pickup_category = target.pickup.pickup_category
            if pickup_category.hinted_as_major or pickup_category.is_key:
                player_name = None
                if players_config.is_multiworld:
                    player_name = players_config.player_names[player_index]

                results[target.pickup].append(
                    OwnedPickupLocation(player_name, PickupLocation(patches.configuration.game, pickup_index))
                )

    return results


def starting_pickups_with_count(patches: GamePatches) -> dict[PickupEntry, int]:
    result = collections.defaultdict(int)

    if not isinstance(patches.starting_equipment, list):
        return {}

    for pickup in patches.starting_equipment:
        result[pickup] += 1

    for pickup in pool_creator.calculate_pool_results(patches.configuration, patches.game).starting:
        result[pickup] -= 1

    return result


def generic_credits(
    standard_pickup_configuration: StandardPickupConfiguration,
    all_patches: dict[int, GamePatches],
    players_config: PlayersConfiguration,
    namer: HintNamer,
    pickup_name_format: str = "{}",
    use_player_color: bool = True,
) -> dict[str, str]:
    major_pickup_name_order = {
        pickup.name: index for index, pickup in enumerate(standard_pickup_configuration.pickups_state.keys())
    }

    def sort_pickup(p: PickupEntry):
        return major_pickup_name_order.get(p.name, math.inf), p.name

    details = get_locations_for_major_pickups_and_keys(all_patches, players_config)
    major_pickups_spoiler = {
        pickup: [entry.export(namer, use_player_color) for entry in entries] for pickup, entries in details.items()
    }

    starting_pickups = starting_pickups_with_count(all_patches[players_config.player_index])
    for pickup, count in starting_pickups.items():
        if count < 1:
            continue

        if pickup not in major_pickups_spoiler:
            major_pickups_spoiler[pickup] = []

        msg = "As a random starting item"
        if count > 1:
            msg += f" ({count} copies)"
        major_pickups_spoiler[pickup].append(msg)

    return {
        pickup_name_format.format(pickup.name): "\n".join(major_pickups_spoiler[pickup]) or "Nowhere"
        for pickup in sorted(major_pickups_spoiler.keys(), key=sort_pickup)
    }


def prime_trilogy_credits(
    standard_pickup_configuration: StandardPickupConfiguration,
    all_patches: dict[int, GamePatches],
    players_config: PlayersConfiguration,
    namer: HintNamer,
    title: str,
    pickup_name_format: str,
) -> str:
    credit_items = generic_credits(
        standard_pickup_configuration, all_patches, players_config, namer, pickup_name_format
    )

    credits_lines = [f"{pickup}\n{location}" for pickup, location in credit_items.items()]

    credits_lines.insert(0, title)
    return "\n\n".join(credits_lines)
