import dataclasses
import uuid
from unittest.mock import MagicMock

from randovania.game_description import default_database
from randovania.games.game import RandovaniaGame
from randovania.gui.lib.signal_handling import set_combo_with_value
from randovania.gui.preset_settings.item_pool_tab import PresetItemPool
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.base.standard_pickup_state import StandardPickupState


def test_on_default_item_updated(skip_qtbot, echoes_game_description, preset_manager):
    # Setup
    game = echoes_game_description.game
    base = preset_manager.default_preset_for_game(game).get_preset()
    preset = dataclasses.replace(base, uuid=uuid.UUID('b41fde84-1f57-4b79-8cd6-3e5a78077fa6'))
    options = MagicMock()

    editor = PresetEditor(preset, options)
    window = PresetItemPool(editor, echoes_game_description, MagicMock())

    pickup_database = default_database.pickup_database_for_game(window.game)
    item = pickup_database.standard_pickups["Dark Beam"]
    category = pickup_database.pickup_categories["beam"]
    combo = window._default_pickups[category]

    # Run
    set_combo_with_value(combo, item)

    # Assert
    assert editor.standard_pickup_configuration.default_pickups[category] == item
    assert editor.standard_pickup_configuration.pickups_state[item] == StandardPickupState(
        num_included_in_starting_pickups=1,
        included_ammo=(50,)
    )
