from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.game_description.db.resource_node import ResourceNode
from randovania.game_description.game_description import GameDescription
from randovania.generator.filler.filler_library import UncollectedState
from randovania.resolver import debug

if TYPE_CHECKING:
    from collections.abc import Iterable

    from randovania.game_description.db.node_identifier import NodeIdentifier
    from randovania.game_description.pickup.pickup_entry import PickupEntry
    from randovania.game_description.resources.pickup_index import PickupIndex
    from randovania.game_description.resources.resource_info import ResourceInfo
    from randovania.generator.filler.player_state import PlayerState
    from randovania.generator.generator_reach import GeneratorReach
    from randovania.graph.state import GraphOrResourceNode
    from randovania.graph.world_graph import WorldGraph


def debug_print_collect_event(event: GraphOrResourceNode) -> None:
    if debug.debug_level() > debug.LogLevel.SILENT:
        print(f"\n--> Collecting {event.full_name()}")


def print_retcon_loop_start(
    player: PlayerState,
    pickups_left: Iterable[PickupEntry],
) -> None:
    if debug.debug_level() > debug.LogLevel.SILENT:
        reach = player.reach
        current_uncollected = UncollectedState.from_reach(reach)
        if debug.debug_level() > debug.LogLevel.NORMAL:
            extra = f", pickups_left:\n{sorted({pickup.name for pickup in pickups_left})}"
        else:
            extra = ""

        print("\n===============================")
        print(
            f"\n>>> {player.name}: "
            f"From {reach.state.node.full_name()}, "
            f"{sum(1 for n in reach.nodes if reach.is_reachable_node(n))} reachable nodes, "
            f"{sum(1 for n in reach.nodes if reach.is_safe_node(n))} safe nodes, "
            f"{len(current_uncollected.pickup_indices)} open pickup indices, "
            f"{len(current_uncollected.events)} open events{extra}"
        )

        if debug.debug_level() > debug.LogLevel.EXTREME:
            print("\nCurrent reach:")
            for node in reach.nodes:
                print(
                    f"[{reach.is_reachable_node(node)!s:>5}, {reach.is_safe_node(node)!s:>5}] "
                    f"{node.identifier.as_string}"
                )


def print_new_resources(
    game: GameDescription | WorldGraph,
    reach: GeneratorReach,
    seen_count: dict[ResourceInfo, int],
    label: str,
) -> None:
    if debug.debug_level() > debug.LogLevel.NORMAL:
        context = reach.node_context()

        if isinstance(game, GameDescription):

            def find_node_with_resource(resource: ResourceInfo) -> GraphOrResourceNode:
                for _, _, node in game.iterate_nodes_of_type(ResourceNode):
                    if node.resource(context) == resource:
                        return node
                raise ValueError(f"Could not find a node with resource {resource}")
        else:

            def find_node_with_resource(resource: ResourceInfo) -> GraphOrResourceNode:
                for node in game.nodes:
                    if any(r == resource for r, _ in node.resource_gain):
                        return node
                raise ValueError(f"Could not find a node with resource {resource}")

        for index, count in seen_count.items():
            if count == 1:
                node = find_node_with_resource(index)
                print(f"-> New {label}: {node.full_name()}")


def print_new_node_identifiers(
    seen_count: dict[NodeIdentifier, int],
    label: str,
) -> None:
    if debug.debug_level() > debug.LogLevel.NORMAL:
        for identifier, count in seen_count.items():
            if count == 1:
                print(f"-> New {label}: {identifier.display_name()}")


def print_new_pickup_index(player: PlayerState, location: PickupIndex) -> None:
    if debug.debug_level() > debug.LogLevel.NORMAL:
        name = player.get_full_name_for_pickup_node_at(location)
        print(f"-> New Pickup Index: {player.name}'s {name}")
