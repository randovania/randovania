from __future__ import annotations

import dataclasses
import uuid
from unittest.mock import MagicMock

from randovania.game.game_enum import RandovaniaGame
from randovania.game_description import default_database
from randovania.games.yokus_island_express.gui.preset_settings.yokus_island_express_goal_tab import PresetYokuGoal
from randovania.games.yokus_island_express.gui.preset_settings.yokus_island_express_patches_tab import (
    PresetYokuPatches,
)
from randovania.interface_common.preset_editor import PresetEditor


def _editor(preset_manager):
    base = preset_manager.default_preset_for_game(RandovaniaGame.YOKUS_ISLAND_EXPRESS).get_preset()
    preset = dataclasses.replace(base, uuid=uuid.UUID("b41fde84-1f57-4b79-8cd6-3e5a78077fa6"))
    return preset, PresetEditor(preset, MagicMock())


def test_starting_fruit_sets_the_configuration(skip_qtbot, preset_manager) -> None:
    game = default_database.game_description_for(RandovaniaGame.YOKUS_ISLAND_EXPRESS)
    preset, editor = _editor(preset_manager)

    tab = PresetYokuPatches(editor, game, MagicMock())
    skip_qtbot.addWidget(tab)
    tab.on_preset_changed(preset)

    # Run
    tab.starting_fruit_spin.setValue(50)

    # Assert
    assert editor.configuration.starting_fruit == 50


def test_starting_fruit_max_settings(skip_qtbot, preset_manager) -> None:
    game = default_database.game_description_for(RandovaniaGame.YOKUS_ISLAND_EXPRESS)
    _, editor = _editor(preset_manager)

    pickup_conf = editor.configuration.standard_pickup_configuration
    wallet = pickup_conf.get_pickup_with_name("Wallet Upgrade")
    with editor:
        editor.set_configuration_field(
            "standard_pickup_configuration",
            pickup_conf.replace_state_for_pickup(
                wallet, dataclasses.replace(pickup_conf.pickups_state[wallet], num_included_in_starting_pickups=2)
            ),
        )

    tab = PresetYokuPatches(editor, game, MagicMock())
    skip_qtbot.addWidget(tab)
    tab.on_preset_changed(editor.create_custom_preset_with())

    # Run
    tab.starting_fruit_spin.setValue(250)

    # Assert: 2 wallet upgrades -> 100 + 2 * 50
    assert tab.starting_fruit_spin.maximum() == 200
    assert editor.configuration.starting_fruit == 200


def test_required_beacons_sets_the_configuration(skip_qtbot, preset_manager) -> None:
    game = default_database.game_description_for(RandovaniaGame.YOKUS_ISLAND_EXPRESS)
    preset, editor = _editor(preset_manager)

    tab = PresetYokuGoal(editor, game, MagicMock())
    skip_qtbot.addWidget(tab)
    tab.on_preset_changed(preset)

    # Run
    tab.required_beacons_spin.setValue(5)

    # Assert
    assert editor.configuration.required_beacons == 5
    assert tab.required_beacons_spin.maximum() == 8
