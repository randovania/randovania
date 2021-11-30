from randovania.games.cave_story.patcher.caver_patcher import CaverPatcher
from randovania.games.game import GameData, GameGenerator, GameGui, GameLayout, GamePresetDescriber

from randovania.games.cave_story.layout.cs_configuration import CSConfiguration
from randovania.games.cave_story.layout.cs_cosmetic_patches import CSCosmeticPatches
from randovania.games.cave_story.layout.preset_describer import cs_format_params, cs_expected_items, cs_unexpected_items, get_ingame_hash_str

def _cs_gui():
    from randovania.games.cave_story.gui.dialog.cs_cosmetic_patches_dialog import CSCosmeticPatchesDialog
    from randovania.games.cave_story.gui.preset_settings import cs_preset_tabs
    from randovania.games.cave_story.item_database import progressive_items

    return GameGui(
        tab_provider=cs_preset_tabs,
        cosmetic_dialog=CSCosmeticPatchesDialog,
        progressive_item_gui_tuples=progressive_items.gui_tuples()
    )

game_data: GameData = GameData(
    short_name="CS",
    long_name="Cave Story",
    experimental=True,

    presets=[
        {
            "path": "starter_preset.rdvpreset"
        }
    ],

    layout=GameLayout(
        configuration=CSConfiguration,
        cosmetic_patches=CSCosmeticPatches,
        preset_describer=GamePresetDescriber(
            expected_items=cs_expected_items,
            unexpected_items=cs_unexpected_items,
            format_params=cs_format_params
        ),
        get_ingame_hash=get_ingame_hash_str
    ),

    gui=_cs_gui,

    generator=GameGenerator(
        item_pool_creator=lambda results, config, db: None
    ),

    patcher=CaverPatcher()
)