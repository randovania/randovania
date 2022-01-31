from randovania.games.game import GameData, GameGenerator, GameGui, GameLayout
from randovania.games.super_metroid.generator.item_pool.pool_creator import super_metroid_specific_pool
from randovania.games.super_metroid.layout.super_metroid_configuration import SuperMetroidConfiguration
from randovania.games.super_metroid.layout.super_metroid_cosmetic_patches import SuperMetroidCosmeticPatches
from randovania.games.super_metroid.patcher.super_duper_metroid_patcher import SuperDuperMetroidPatcher
from randovania.generator.base_patches_factory import BasePatchesFactory
from randovania.resolver.bootstrap import Bootstrap


def _super_metroid_gui():
    from randovania.games.super_metroid.gui.preset_settings import super_metroid_preset_tabs
    from randovania.games.super_metroid.gui.dialog.super_cosmetic_patches_dialog import SuperCosmeticPatchesDialog

    return GameGui(
        tab_provider=super_metroid_preset_tabs,
        cosmetic_dialog=SuperCosmeticPatchesDialog,
        input_file_text=("an SFC/SMC file", "the Super Famicom/SNES", "SFC/SMC"),
    )


game_data: GameData = GameData(
    short_name="SM",
    long_name="Super Metroid",
    experimental=True,

    presets=[
        {
            "path": "starter_preset.rdvpreset"
        }
    ],

    faq={
    }.items(),

    layout=GameLayout(
        configuration=SuperMetroidConfiguration,
        cosmetic_patches=SuperMetroidCosmeticPatches
    ),

    gui=_super_metroid_gui,

    generator=GameGenerator(
        item_pool_creator=super_metroid_specific_pool,
        bootstrap=Bootstrap(),
        base_patches_factory=BasePatchesFactory()
    ),

    patcher=SuperDuperMetroidPatcher()
)
