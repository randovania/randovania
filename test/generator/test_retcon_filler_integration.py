from random import Random
from unittest.mock import MagicMock

import pytest

from randovania.game_description import data_reader
from randovania.generator.filler import retcon
from randovania.layout.layout_configuration import LayoutConfiguration
from randovania.resolver.bootstrap import logic_bootstrap


@pytest.mark.skip
@pytest.mark.skip_generation_tests
def test_retcon_filler_integration(default_layout_configuration):
    layout_configuration = default_layout_configuration

    rng = Random("fixed-seed!")
    status_update = MagicMock()

    game = data_reader.decode_data(layout_configuration.game_data)
    patches = game.create_game_patches()
    available_pickups = game.pickup_database.all_useful_pickups

    new_game, state = logic_bootstrap(layout_configuration, game, patches)
    new_game.patch_requirements(state.resources, layout_configuration.damage_strictness.value)

    filler_patches = retcon.retcon_playthrough_filler(new_game,
                                                      state, tuple(available_pickups), rng,
                                                      0, 0,
                                                      status_update)
    assert filler_patches == patches
