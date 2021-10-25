from randovania.games.game import GameData, GameGenerator, GameGui, GameLayout, GamePresetDescriber

from randovania.layout.base.base_configuration import BaseConfiguration
from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches

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
        configuration=BaseConfiguration,
        cosmetic_patches=BaseCosmeticPatches
    ),

    gui=_dread_gui,

    generator=GameGenerator(
        item_pool_creator=lambda results, config, db: None
    )
)