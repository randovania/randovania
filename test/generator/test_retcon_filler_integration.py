from random import Random
from unittest.mock import MagicMock

import pytest

from randovania.game_description import data_reader
from randovania.game_description.game_patches import GamePatches
from randovania.generator.filler import retcon
from randovania.layout.layout_configuration import LayoutConfiguration
from randovania.resolver.bootstrap import logic_bootstrap

skip_generation_tests = pytest.mark.skipif(
    pytest.config.option.skip_generation_tests,
    reason="skipped due to --skip-generation-tests")


@skip_generation_tests
@pytest.mark.skip
def test_retcon_filler_integration():
    layout_configuration = LayoutConfiguration.default()

    rng = Random("fixed-seed!")
    status_update = MagicMock()

    game = data_reader.decode_data(layout_configuration.game_data)
    patches = GamePatches.with_game(game)
    available_pickups = game.pickup_database.all_useful_pickups

    new_game, state = logic_bootstrap(layout_configuration, game, patches)
    new_game.simplify_connections(state.resources)

    filler_patches = retcon.retcon_playthrough_filler(new_game,
                                                      state, tuple(available_pickups), rng,
                                                      0, 0,
                                                      status_update)
    assert filler_patches == patches

