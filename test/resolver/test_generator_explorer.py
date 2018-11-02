from typing import Tuple, List, Iterator

import pytest

from randovania.game_description import data_reader
from randovania.game_description.node import Node, ResourceNode
from randovania.games.prime import binary_data
from randovania.resolver.bootstrap import logic_bootstrap
from randovania.resolver.game_patches import GamePatches
from randovania.resolver.generator_explorer import PathDetail, GeneratorReach, filter_reachable, filter_uncollected, \
    filter_resource_nodes, filter_out_dangerous_actions
from randovania.resolver.layout_configuration import LayoutConfiguration, LayoutLogic, LayoutMode, LayoutRandomizedFlag, \
    LayoutEnabledFlag, LayoutDifficulty
from randovania.resolver.logic import Logic
from randovania.resolver.state import State


@pytest.mark.parametrize(["old_path", "new_path", "expected"], [
    (PathDetail(True, 0), PathDetail(True, 0), False),
    (PathDetail(False, 0), PathDetail(False, 0), False),
    (PathDetail(True, 0), PathDetail(True, 1), False),
    (PathDetail(True, 5), PathDetail(False, 0), False),
    (PathDetail(False, 0), PathDetail(True, 5), True),
])
def test_is_path_better(old_path: PathDetail, new_path: PathDetail, expected: bool):
    assert new_path.is_better(old_path) == expected


def _uncollected_resources(nodes: Iterator[Node], state: State) -> Iterator[ResourceNode]:
    return filter_uncollected(filter_resource_nodes(nodes), state)


def _gimme_reach(logic: Logic, initial_state: State, patches: GamePatches) -> Tuple[GeneratorReach, List[ResourceNode]]:
    reach = GeneratorReach(logic, initial_state)
    actions = []

    while True:
        safe_actions = [
            action for action in
            filter_out_dangerous_actions(
                _uncollected_resources(
                    filter_reachable(reach.safe_nodes, reach),
                    reach.state),
                logic.game
            )
        ]
        # print("=== Found {} safe actions".format(len(safe_actions)))
        if not safe_actions:
            break

        for action in safe_actions:
            # print("== Collecting safe resource at {}".format(logic.game.node_name(action)))
            reach.advance_to(reach.state.act_on_node(action, patches.pickup_mapping))
            assert set(reach.nodes) == set(GeneratorReach(logic, reach.state).nodes)

    # print(">>>>>>>> Actions from {}:".format(logic.game.node_name(reach.state.node)))
    for node in _uncollected_resources(filter_reachable(reach.nodes, reach), reach.state):
        actions.append(node)
        # print("++ Safe? {1} -- {0}".format(logic.game.node_name(node), reach.is_safe_node(node)))

    # print("Progression:\n * {}".format(
    #     "\n * ".join(sorted(str(resource) for resource in reach.progression_resources))
    # ))

    return reach, actions


def _do_stuff(logic: Logic, state: State, patches: GamePatches):
    for i in range(7):
        # print("\n>>> STEP {}".format(i))
        reach, actions = _gimme_reach(logic, state, patches)
        state = state.act_on_node(actions[0], patches.pickup_mapping)


def test_calculate_reach():
    data = binary_data.decode_default_prime2()
    game = data_reader.decode_data(data, [], False)
    configuration = LayoutConfiguration(logic=LayoutLogic.NO_GLITCHES,
                                        mode=LayoutMode.STANDARD,
                                        sky_temple_keys=LayoutRandomizedFlag.RANDOMIZED,
                                        item_loss=LayoutEnabledFlag.ENABLED,
                                        elevators=LayoutRandomizedFlag.VANILLA,
                                        hundo_guaranteed=LayoutEnabledFlag.DISABLED,
                                        difficulty=LayoutDifficulty.NORMAL,
                                        pickup_quantities={})

    patches = GamePatches(
        configuration.item_loss == LayoutEnabledFlag.ENABLED,
        [None] * len(game.resource_database.pickups)
    )
    logic, state = logic_bootstrap(configuration, game, patches)
    _do_stuff(logic, state, patches)
