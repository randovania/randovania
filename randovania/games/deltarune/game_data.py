from randovania.games import game
from randovania.games.deltarune import generator, layout
from randovania.games.deltarune import patcherfolder


def _gui() -> game.GameGui:
    from randovania.games.deltarune import gui

    return game.GameGui(
        tab_provider=gui.preset_tabs,
        cosmetic_dialog=gui.deltaruneCosmeticPatchesDialog,
        progressive_item_gui_tuples=tuple(),
        input_file_text=("a data.win file", "the DELTARUNE", "data.win file"),
        spoiler_visualizer=tuple(),
    )


game_data: game.GameData = game.GameData(
    short_name="Deltarune",
    long_name="Deltarune",
    experimental=True,

    presets=[
        {
            "path": "starter_preset.rdvpreset"
        },
    ],

    faq=[],

    layout=game.GameLayout(
        configuration=layout.deltaruneConfiguration,
        cosmetic_patches=layout.deltaruneCosmeticPatches,
    ),

    gui=_gui,

    generator=game.GameGenerator(
        item_pool_creator=generator.pool_creator,
        bootstrap=generator.deltaruneBootstrap(),
        base_patches_factory=generator.deltaruneBasePatchesFactory(),
    ),

    patcher=patcherfolder.PatcherMaker(),
)
