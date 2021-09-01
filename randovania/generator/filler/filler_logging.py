from typing import Iterator, Dict

from randovania.game_description.game_description import GameDescription
from randovania.game_description.world.node import ResourceNode
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.resource_info import ResourceInfo
from randovania.generator.filler.filler_library import UncollectedState, find_node_with_resource
from randovania.generator.generator_reach import GeneratorReach
from randovania.resolver import debug


def debug_print_collect_event(event: ResourceNode, game: GameDescription):
    if debug.debug_level() > 0:
        print("\n--> Collecting {}".format(game.world_list.node_name(event, with_world=True)))


def print_retcon_loop_start(game: GameDescription,
                            pickups_left: Iterator[PickupEntry],
                            reach: GeneratorReach,
                            player_index: int,
                            ):
    if debug.debug_level() > 0:
        current_uncollected = UncollectedState.from_reach(reach)
        if debug.debug_level() > 1:
            extra = ", pickups_left:\n{}".format(sorted(set(pickup.name for pickup in pickups_left)))
        else:
            extra = ""

        print("\n===============================")
        print("\n>>> Player {}: From {}, {} open pickup indices, {} open events{}".format(
            player_index,
            game.world_list.node_name(reach.state.node, with_world=True),
            len(current_uncollected.indices),
            len(current_uncollected.events),
            extra
        ))

        if debug.debug_level() > 2:
            print("\nCurrent reach:")
            for node in reach.nodes:
                print("[{!s:>5}, {!s:>5}] {}".format(reach.is_reachable_node(node), reach.is_safe_node(node),
                                                     game.world_list.node_name(node)))


def print_new_resources(game: GameDescription,
                        reach: GeneratorReach,
                        seen_count: Dict[ResourceInfo, int],
                        label: str,
                        ):
    world_list = game.world_list
    if debug.debug_level() > 1:
        for index, count in seen_count.items():
            if count == 1:
                node = find_node_with_resource(index, world_list.all_nodes)
                print("-> New {}: {}".format(label, world_list.node_name(node, with_world=True)))
