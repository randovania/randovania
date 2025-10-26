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
    world_name: str | None
    location: PickupLocation

    def export(self, namer: HintNamer, use_player_color: bool = True) -> str:
        hint = namer.format_location(self.location, with_region=True, with_area=True, with_color=False)
        if self.world_name is not None:
            hint = f"{namer.format_world(self.world_name, with_color=use_player_color)}'s {hint}"
        return hint


def get_locations_for_major_pickups_and_keys(
    all_patches: dict[int, GamePatches],
    players_config: PlayersConfiguration,
) -> dict[PickupEntry, list[OwnedPickupLocation | str]]:  # Technically inaccurate return type, but makes typing easier.
    results: dict[PickupEntry, list[OwnedPickupLocation | str]] = collections.defaultdict(list)

    for player_index, patches in all_patches.items():
        for pickup_index, target in patches.pickup_assignment.items():
            if target.player != players_config.player_index:
                continue

            if target.pickup.show_in_credits_spoiler:
                player_name = None
                if players_config.is_multiworld:
                    player_name = players_config.player_names[player_index]

                results[target.pickup].append(
                    OwnedPickupLocation(player_name, PickupLocation(patches.configuration.game, pickup_index))
                )

    return results


def starting_pickups_with_count(patches: GamePatches) -> dict[PickupEntry, int]:
    result: dict[PickupEntry, int] = collections.defaultdict(int)

    if not isinstance(patches.starting_equipment, list):
        return {}

    for pickup in patches.starting_equipment:
        if pickup.show_in_credits_spoiler:
            result[pickup] += 1

    for pickup in pool_creator.calculate_pool_results(patches.configuration, patches.game).starting:
        if pickup.show_in_credits_spoiler:
            result[pickup] -= 1

    return result


def generic_credits(
    standard_pickup_configuration: StandardPickupConfiguration,
    all_patches: dict[int, GamePatches],
    players_config: PlayersConfiguration,
) -> list[tuple[PickupEntry, list[OwnedPickupLocation | str]]]:
    """
    Returns the credits in the form of a list of tuples that can be used to create your own formatting.
    The first tuple element will be a PickupEntry, and the second tuple element a list of location entries.
    An entry is either an OwnedPickupLocation if the pickup is located somewhere, or a string which
    is used for special cases (such as starting with the pickup).
    """
    major_pickup_name_order = {
        pickup.name: index for index, pickup in enumerate(standard_pickup_configuration.pickups_state.keys())
    }

    def sort_pickup(tup: tuple[PickupEntry, list[OwnedPickupLocation | str]]) -> tuple[float, str]:
        p = tup[0]
        return major_pickup_name_order.get(p.name, math.inf), p.name

    details = get_locations_for_major_pickups_and_keys(all_patches, players_config)

    starting_pickups = starting_pickups_with_count(all_patches[players_config.player_index])
    for pickup, count in starting_pickups.items():
        if count < 1:
            continue

        if pickup not in details:
            details[pickup] = []

        msg = "As a random starting item"
        if count > 1:
            msg += f" ({count} copies)"
        details[pickup].append(msg)

    # FIXME: should get triggered on excluded pickups, but doesn't right now
    for pickup, entries in details.items():
        if not entries:
            entries.append("Nowhere")

    return sorted(details.items(), key=sort_pickup)


def generic_string_credits(
    standard_pickup_configuration: StandardPickupConfiguration,
    all_patches: dict[int, GamePatches],
    players_config: PlayersConfiguration,
    namer: HintNamer,
    pickup_name_format: str = "{}",
    use_player_color: bool = True,
) -> dict[str, str]:
    """
    Returns the credits in the form of a simple-to-plug formatted dictionary.
    The key will be a pickup name formatted via `pickup_name_format`, the key a string detailing all the locations
    formatted via `namer` and `use_player_color` and separated with a newline.
    """
    details = generic_credits(standard_pickup_configuration, all_patches, players_config)

    pickup_to_strings = {
        pickup: [
            entry.export(namer, use_player_color) if isinstance(entry, OwnedPickupLocation) else entry
            for entry in entries
        ]
        for pickup, entries in details
    }

    return {pickup_name_format.format(pickup.name): "\n".join(text) for pickup, text in pickup_to_strings.items()}


def prime_trilogy_credits(
    standard_pickup_configuration: StandardPickupConfiguration,
    all_patches: dict[int, GamePatches],
    players_config: PlayersConfiguration,
    namer: HintNamer,
    title: str,
    pickup_name_format: str,
) -> str:
    credit_items = generic_string_credits(
        standard_pickup_configuration, all_patches, players_config, namer, pickup_name_format
    )

    credits_lines = [f"{pickup}\n{location}" for pickup, location in credit_items.items()]

    credits_lines.insert(0, title)
    return "\n\n".join(credits_lines)
