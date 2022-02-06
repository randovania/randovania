from randovania.games import game
from randovania.games.blank import generator, layout


def _gui() -> game.GameGui:
    from randovania.games.blank import gui

    return game.GameGui(
        tab_provider=gui.preset_tabs,
        cosmetic_dialog=gui.BlankCosmeticPatchesDialog,
        progressive_item_gui_tuples=tuple(),
        spoiler_visualizer=tuple(),
    )


game_data: game.GameData = game.GameData(
    short_name="Blank",
    long_name="Blank Development Game",
    experimental=True,

    presets=[
        {
            "path": "starter_preset.rdvpreset"
        },
    ],

    faq=[],

    layout=game.GameLayout(
        configuration=layout.BlankConfiguration,
        cosmetic_patches=layout.BlankCosmeticPatches,
    ),

    gui=_gui,

    generator=game.GameGenerator(
        item_pool_creator=generator.pool_creator,
        bootstrap=generator.BlankBootstrap(),
        base_patches_factory=generator.BlankBasePatchesFactory(),
    ),

    patcher=None,
)
