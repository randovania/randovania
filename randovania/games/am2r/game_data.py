from randovania.games import game
from randovania.games.am2r import layout
from randovania.layout.preset_describer import GamePresetDescriber

def _options():
    from randovania.interface_common.options import PerGameOptions
    return PerGameOptions


def _gui() -> game.GameGui:
    from randovania.games.am2r import gui

    return game.GameGui(
        game_tab=gui.AM2RGameTabWidget,
        tab_provider=gui.preset_tabs,
        cosmetic_dialog=gui.AM2RCosmeticPatchesDialog,
        export_dialog=gui.AM2RGameExportDialog,
        progressive_item_gui_tuples=tuple(),
        spoiler_visualizer=tuple(),
    )


def _generator() -> game.GameGenerator:
    from randovania.games.am2r import generator
    from randovania.generator.hint_distributor import AllJokesHintDistributor

    return game.GameGenerator(
        item_pool_creator=generator.pool_creator,
        bootstrap=generator.AM2RBootstrap(),
        base_patches_factory=generator.AM2RBasePatchesFactory(),
        hint_distributor=AllJokesHintDistributor(),
    )


def _patch_data_factory():
    from randovania.games.am2r.exporter.patch_data_factory import AM2RPatchDataFactory
    return AM2RPatchDataFactory


def _exporter():
    from randovania.games.am2r.exporter.game_exporter import AM2RGameExporter
    return AM2RGameExporter()

game_data: game.GameData = game.GameData(
    short_name="AM2R",
    long_name="Another Metroid 2 Remake",
    development_state=game.DevelopmentState.EXPERIMENTAL,

    presets=[
        {
            "path": "starter_preset.rdvpreset"
        },
    ],

    faq=[],

    layout=game.GameLayout(
        configuration=layout.AM2RConfiguration,
        cosmetic_patches=layout.AM2RCosmeticPatches,
        preset_describer=GamePresetDescriber(),
    ),

    options=_options,

    gui=_gui,

    generator=_generator,

    patch_data_factory=_patch_data_factory,

    exporter=_exporter,

    multiple_start_nodes_per_area=False,
)
