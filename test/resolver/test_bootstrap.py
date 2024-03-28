from __future__ import annotations

from random import Random

from randovania.game_description import default_database


def test_logic_bootstrap(preset_manager, game_enum):
    configuration = preset_manager.default_preset_for_game(game_enum).get_preset().configuration
    game = default_database.game_description_for(configuration.game)

    patches = game_enum.generator.base_patches_factory.create_base_patches(configuration, Random(1000), game, False, 0)

    new_game, state = game_enum.generator.bootstrap.logic_bootstrap(
        configuration,
        game.get_mutable(),
        patches,
    )

    for misc_resource in game.resource_database.misc:
        assert state.resources.is_resource_set(misc_resource)

    assert state.node.identifier == configuration.starting_location.locations[0]
