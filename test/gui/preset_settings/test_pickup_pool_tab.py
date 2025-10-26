from __future__ import annotations

import dataclasses
import uuid
from unittest.mock import MagicMock

import pytest

from randovania.game_description import default_database
from randovania.gui.lib.signal_handling import set_combo_with_value
from randovania.gui.preset_settings.pickup_pool_tab import PresetPickupPool
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.base.available_locations import RandomizationMode
from randovania.layout.base.standard_pickup_state import StandardPickupState


def test_on_default_pickup_updated(skip_qtbot, echoes_game_description, preset_manager):
    # Setup
    game = echoes_game_description.game
    base = preset_manager.default_preset_for_game(game).get_preset()
    preset = dataclasses.replace(base, uuid=uuid.UUID("b41fde84-1f57-4b79-8cd6-3e5a78077fa6"))
    options = MagicMock()

    editor = PresetEditor(preset, options)
    window = PresetPickupPool(editor, echoes_game_description, MagicMock())

    pickup_database = default_database.pickup_database_for_game(window.game)
    pickup = pickup_database.standard_pickups["Dark Beam"]
    category = pickup_database.pickup_categories["beam"]
    combo = window._default_pickups[category]

    # Run
    set_combo_with_value(combo, pickup)

    # Assert
    assert editor.standard_pickup_configuration.default_pickups[category] == pickup
    assert editor.standard_pickup_configuration.pickups_state[pickup] == StandardPickupState(
        num_included_in_starting_pickups=1, included_ammo=(50,)
    )


@pytest.mark.parametrize("randomization_mode", RandomizationMode)
def test_pickup_pool_count_label(
    skip_qtbot, blank_game_description, preset_manager, randomization_mode: RandomizationMode
):
    base = preset_manager.default_preset_for_game(blank_game_description.game).get_preset()
    preset = dataclasses.replace(
        base,
        uuid=uuid.UUID("b41fde84-1f57-4b79-8cd6-3e5a78077fa6"),
        configuration=dataclasses.replace(
            base.configuration,
            available_locations=dataclasses.replace(
                base.configuration.available_locations,
                randomization_mode=randomization_mode,
            ),
            standard_pickup_configuration=dataclasses.replace(
                base.configuration.standard_pickup_configuration,
                minimum_random_starting_pickups=1,
            ),
        ),
    )
    options = MagicMock()
    editor = PresetEditor(preset, options)
    window = PresetPickupPool(editor, blank_game_description, MagicMock())

    # Run
    window.on_preset_changed(preset)

    # Assert
    message = "Items in pool: 8/9"
    if randomization_mode is RandomizationMode.MAJOR_MINOR_SPLIT:
        message += "<br />Major: 6/6 - Minor: 2/2 - Starting: 1"

    assert window.pickup_pool_count_label.text() == message
