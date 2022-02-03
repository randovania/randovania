from randovania.games.game import GameData, GameGenerator, GameGui, GameLayout, GamePresetDescriber
from randovania.games.deltarune.generator.bootstrap import deltaruneBootstrap
from randovania.games.deltarune.generator.item_pool.pool_creator import deltarune_specific_pool
from randovania.games.deltarune.layout.preset_describer import deltarune_expected_items, deltarune_unexpected_items, \
    deltarune_format_params
from randovania.games.deltarune.layout.deltarune_configuration import deltaruneConfiguration
from randovania.games.deltarune.layout.deltarune_cosmetic_patches import deltaruneCosmeticPatches
from randovania.generator.base_patches_factory import BasePatchesFactory

def _deltarune_gui():
    from randovania.games.deltarune.gui.preset_settings import deltarune_preset_tabs
    from randovania.games.deltarune.gui.dialog.deltarune_cosmetic_patches_dialog import deltaruneCosmeticPatchesDialog
    from randovania.gui.game_details.teleporter_details_tab import TeleporterDetailsTab

    return GameGui(
        tab_provider=deltarune_preset_tabs,
        cosmetic_dialog=deltaruneCosmeticPatchesDialog,
        input_file_text=("an ISO file", "the Nintendo Gamecube", "Gamecube ISO"),
        spoiler_visualizer=(TeleporterDetailsTab,),
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

    faq=[
        ("Why are there shiny spots blocking paths?",

         "Those spots are to add progression to this linear game."),

    ],

    layout=GameLayout(
        configuration=deltaruneConfiguration,
        cosmetic_patches=deltaruneCosmeticPatches,
        preset_describer=GamePresetDescriber(
            expected_items=deltarune_expected_items,
            unexpected_items=deltarune_unexpected_items,
            format_params=deltarune_format_params
        )
    ),

    gui=_deltarune_gui,

    generator=GameGenerator(
        item_pool_creator=deltarune_specific_pool,
        bootstrap=deltaruneBootstrap(),
        base_patches_factory=BasePatchesFactory()
    ),
)
