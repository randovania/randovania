import dataclasses
import uuid

from randovania.game_description import default_database
from randovania.games.game import RandovaniaGame
from randovania.gui.preset_settings.item_pool_tab import PresetItemPool
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.base.major_item_state import MajorItemState


def test_on_default_item_updated(skip_qtbot, preset_manager):
    # Setup
    game = RandovaniaGame.METROID_PRIME_ECHOES
    base = preset_manager.default_preset_for_game(game).get_preset()
    preset = dataclasses.replace(base,
                                 uuid=uuid.UUID('b41fde84-1f57-4b79-8cd6-3e5a78077fa6'),
                                 base_preset_uuid=base.uuid)

    editor = PresetEditor(preset)
    window = PresetItemPool(editor)

    item_database = default_database.item_database_for_game(window.game)
    item = item_database.major_items["Dark Beam"]
    category = item_database.item_categories["beam"]
    combo = window._default_items[category]

    # Run
    combo.setCurrentIndex(combo.findData(item))

    # Assert
    assert editor.major_items_configuration.default_items[category] == item
    assert editor.major_items_configuration.items_state[item] == MajorItemState(
        num_included_in_starting_items=1,
        included_ammo=(50,)
    )
