from randovania.games.deltarune import generator
from randovania.games.deltarune.layout.deltarune_configuration import deltaruneConfiguration
from randovania.games.deltarune.layout.deltarune_cosmetic_patches import deltaruneCosmeticPatches
from randovania.games.game import GameData, GameGenerator, GameGui, GameLayout


def _gui():
    from randovania.games.deltarune.gui import preset_settings, deltaruneCosmeticPatchesDialog

    return GameGui(
        tab_provider=preset_settings.preset_tabs,
        cosmetic_dialog=deltaruneCosmeticPatchesDialog,
        progressive_item_gui_tuples=tuple(),
        spoiler_visualizer=tuple(),
    )


game_data: GameData = GameData(
    short_name="Deltarune",
    long_name="Deltarune",
    experimental=True,

    presets=[
        {
            "path": "starter_preset.rdvpreset"
        },
    ],

    faq=[],

    layout=GameLayout(
        configuration=deltaruneConfiguration,
        cosmetic_patches=deltaruneCosmeticPatches,
    ),

    gui=_gui,

    generator=GameGenerator(
        item_pool_creator=generator.pool_creator,
        bootstrap=generator.deltaruneBootstrap(),
        base_patches_factory=generator.deltaruneBasePatchesFactory(),
    ),

    patcher=None,
)
