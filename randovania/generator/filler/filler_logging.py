from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.generator.filler.filler_library import UncollectedState, find_node_with_resource
from randovania.resolver import debug

if TYPE_CHECKING:
    from collections.abc import Iterable

    from randovania.game_description.db.node_identifier import NodeIdentifier
    from randovania.game_description.pickup.pickup_entry import PickupEntry
    from randovania.game_description.resources.pickup_index import PickupIndex
    from randovania.game_description.resources.resource_info import ResourceInfo
    from randovania.generator.filler.player_state import PlayerState
    from randovania.graph.world_graph import WorldGraph, WorldGraphNode


def debug_print_collect_event(event: WorldGraphNode) -> None:
    if debug.debug_level() > 0:
        print(f"\n--> Collecting {event.name}")


def print_retcon_loop_start(
    player: PlayerState,
    pickups_left: Iterable[PickupEntry],
) -> None:
    if debug.debug_level() > 0:
        reach = player.reach
        current_uncollected = UncollectedState.from_reach(reach)
        if debug.debug_level() > 1:
            extra = f", pickups_left:\n{sorted({pickup.name for pickup in pickups_left})}"
        else:
            extra = ""

        print("\n===============================")
        print(
            f"\n>>> {player.name}: "
            f"From {reach.state.node.name}, "
            f"{sum(1 for n in reach.nodes if reach.is_reachable_node(n))} reachable nodes, "
            f"{sum(1 for n in reach.nodes if reach.is_safe_node(n))} safe nodes, "
            f"{len(current_uncollected.indices)} open pickup indices, "
            f"{len(current_uncollected.events)} open events{extra}"
        )

        if debug.debug_level() > 2:
            print("\nCurrent reach:")
            for node in reach.nodes:
                print(f"[{reach.is_reachable_node(node)!s:>5}, {reach.is_safe_node(node)!s:>5}] " f"{node.name}")


def print_new_resources(
    world_graph: WorldGraph,
    seen_count: dict[ResourceInfo, int],
    label: str,
) -> None:
    if debug.debug_level() > 1:
        for index, count in seen_count.items():
            if count == 1:
                node = find_node_with_resource(index, world_graph.nodes)
                print(f"-> New {label}: {node.name}")


def print_new_node_identifiers(seen_count: dict[NodeIdentifier, int], label: str) -> None:
    if debug.debug_level() > 1:
        for identifier, count in seen_count.items():
            if count == 1:
                print(f"-> New {label}: {identifier.as_string}")


def print_new_pickup_index(player: PlayerState, location: PickupIndex) -> None:
    if debug.debug_level() > 1:
        node = player.world_graph.node_by_pickup_index[location]
        print(f"-> New Pickup Index: {player.name}'s {node.identifier.as_string}")
