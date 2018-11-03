import pytest

from randovania.game_description import data_reader
from randovania.games.prime import binary_data
from randovania.resolver.bootstrap import logic_bootstrap
from randovania.resolver.game_patches import GamePatches
from randovania.resolver.generator import gimme_reach, get_actions_of_reach
from randovania.resolver.generator_explorer import PathDetail
from randovania.resolver.layout_configuration import LayoutConfiguration, LayoutLogic, LayoutMode, LayoutRandomizedFlag, \
    LayoutEnabledFlag, LayoutDifficulty


@pytest.mark.parametrize(["old_path", "new_path", "expected"], [
    (PathDetail(True, 0), PathDetail(True, 0), False),
    (PathDetail(False, 0), PathDetail(False, 0), False),
    (PathDetail(True, 0), PathDetail(True, 1), False),
    (PathDetail(True, 5), PathDetail(False, 0), False),
    (PathDetail(False, 0), PathDetail(True, 5), True),
])
def test_is_path_better(old_path: PathDetail, new_path: PathDetail, expected: bool):
    assert new_path.is_better(old_path) == expected


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

    for pickup in game.resource_database.pickups:
        for resource, quantity in pickup.resource_gain(logic.game.resource_database):
            state.resources[resource] = state.resources.get(resource, 0)
            state.resources[resource] += quantity

    first_reach = gimme_reach(logic, state, patches)

    second_reach = gimme_reach(logic, first_reach.state, patches)

    first_actions = get_actions_of_reach(first_reach)
    second_actions = get_actions_of_reach(second_reach)

    assert (len(list(first_reach.nodes)), len(first_actions)) == (554, 17)
    assert (len(list(second_reach.nodes)), len(second_actions)) == (554, 17)
    # (549, 36)
    # (554, 17)

    assert set(first_reach.safe_nodes) == set(second_reach.safe_nodes)
    assert set(first_actions) == set(second_actions)
    assert set(first_reach.nodes) == set(second_reach.nodes)
