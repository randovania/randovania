import pytest

from randovania.game_description import data_reader
from randovania.games.prime import binary_data
from randovania.resolver import generator_explorer
from randovania.resolver.bootstrap import logic_bootstrap
from randovania.resolver.game_patches import GamePatches
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

    logic, state = logic_bootstrap(configuration, game, GamePatches(True, []))

    reach = generator_explorer.GeneratorReach(logic, state)
    print(reach)
    assert False

