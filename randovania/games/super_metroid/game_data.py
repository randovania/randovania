from randovania.games.game import GameData, GameGenerator, GameGui, GameLayout
from randovania.games.super_metroid.generator.item_pool.pool_creator import super_metroid_specific_pool
from randovania.games.super_metroid.layout.super_metroid_configuration import SuperMetroidConfiguration
from randovania.games.super_metroid.layout.super_metroid_cosmetic_patches import SuperMetroidCosmeticPatches
from randovania.games.super_metroid.patcher.super_duper_metroid_patcher import SuperDuperMetroidPatcher
from randovania.generator.base_patches_factory import BasePatchesFactory
from randovania.resolver.bootstrap import Bootstrap


def _super_metroid_gui():
    from randovania.games.super_metroid.gui.dialog.super_cosmetic_patches_dialog import SuperCosmeticPatchesDialog
    from randovania.games.super_metroid.gui.preset_settings import super_metroid_preset_tabs
    from randovania.games.super_metroid.gui.super_metroid_help_widget import SuperMetroidHelpWidget

    return GameGui(
        tab_provider=super_metroid_preset_tabs,
        cosmetic_dialog=SuperCosmeticPatchesDialog,
        input_file_text=("an SFC/SMC file", "the Super Famicom/SNES", "SFC/SMC"),
        help_widget=lambda: SuperMetroidHelpWidget(),
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

    faq=[
        ("What glitches are accounted for in logic?",
         "Mostly none at the moment. There are a few, but this is a work in progress. "
         "Once implemented, players will be able to enable or disable any category of tricks by setting a "
         "difficulty for each trick category in the preset."),

        ("How do I adjust heatrun logic?",
         "There is no heatrun logic, but when that's added you will be able to set a scale for how much health "
         "you're expected to have to perform heat runs, as well as setting a trick difficulty that can outright "
         "disable more complex ones. This is not yet a feature."),

        ("What version of the game should I play on?",
         "The NTSC version is what you should use. NTSC-U and NTSC-J are actually identical, so it doesn't matter "
         "which you use. The PAL version is not supported."),

        ("What can be randomized?",
         "You can randomize the game's items, as well as starting items and spawn location. "
         "You can only spawn in Vanilla save stations, at the ship, or at Ceres Station. "
         "Item rando can be done as either major/minor or full rando. "
         "You cannot randomize room or area layout, door caps, bosses, escape, or anything else, "
         "though these are planned for the future."),

        ("What patches are supported?",
         "There are many patches, both gameplay patches (which can be selected in the preset settings) and "
         "cosmetic patches (which can be chosen in the cosmetic patches dialogue after generating a game). "
         "There is no support for custom Samus or Ship sprites at the moment, though this is planned for future."),

        ("Will you support multiworld?",
         "This is planned in future. Much of the work on the game interface has already been done, "
         "but there's more work that needs to be done to integrate the game with Randovania."),

        ("Will you support SMZ3?",
         "No."),
    ],

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
