from __future__ import annotations

import dataclasses

from randovania.game_description import default_database


def test_logic_bootstrap(preset_manager, game_enum, empty_patches):
    configuration = preset_manager.default_preset_for_game(game_enum).get_preset().configuration
    game = default_database.game_description_for(configuration.game)

    new_game, state = game_enum.generator.bootstrap.logic_bootstrap(
        configuration,
        game.get_mutable(),
        dataclasses.replace(empty_patches, configuration=configuration, starting_location=game.starting_location),
    )

    for misc_resource in game.resource_database.misc:
        assert state.resources.is_resource_set(misc_resource)

    assert state.node.identifier == game.starting_location
