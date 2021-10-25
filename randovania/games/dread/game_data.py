from randovania.games.game import GameData, GameGenerator, GameGui, GameLayout, GamePresetDescriber

from randovania.games.dread.layout.dread_configuration import DreadConfiguration
from randovania.games.dread.layout.dread_cosmetic_patches import DreadCosmeticPatches
from randovania.games.dread.layout.preset_describer import dread_format_params, dread_expected_items, dread_unexpected_items

def _dread_gui():
    pass

game_data: GameData = GameData(
    short_name="Dread",
    long_name="Metroid Dread",
    experimental=True,

    presets=[
        {
            "path": "starter_preset.rdvpreset"
        }
    ],

    layout=GameLayout(
        configuration=DreadConfiguration,
        cosmetic_patches=DreadCosmeticPatches,
        preset_describer=GamePresetDescriber(
            expected_items=dread_expected_items,
            unexpected_items=dread_unexpected_items,
            format_params=dread_format_params
        )
    ),

    gui=_dread_gui,

    generator=GameGenerator(
        item_pool_creator=lambda results, config, db: None
    )
)