from randovania.games.blank import generator
from randovania.games.blank.layout.blank_configuration import BlankConfiguration
from randovania.games.blank.layout.blank_cosmetic_patches import BlankCosmeticPatches
from randovania.games.game import GameData, GameGenerator, GameGui, GameLayout


def _gui():
    from randovania.games.blank.gui import preset_settings, BlankCosmeticPatchesDialog

    return GameGui(
        tab_provider=preset_settings.preset_tabs,
        cosmetic_dialog=BlankCosmeticPatchesDialog,
        progressive_item_gui_tuples=tuple(),
        spoiler_visualizer=tuple(),
    )


game_data: GameData = GameData(
    short_name="Blank",
    long_name="Blank Development Game",
    experimental=True,

    presets=[
        {
            "path": "starter_preset.rdvpreset"
        },
    ],

    faq=[],

    layout=GameLayout(
        configuration=BlankConfiguration,
        cosmetic_patches=BlankCosmeticPatches,
    ),

    gui=_gui,

    generator=GameGenerator(
        item_pool_creator=generator.pool_creator,
        bootstrap=generator.BlankBootstrap(),
        base_patches_factory=generator.BlankBasePatchesFactory(),
    ),

    patcher=None,
)
