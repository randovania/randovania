from __future__ import annotations

import randovania
from randovania.games import game
from randovania.games.metroid import layout
from randovania.layout.preset_describer import GamePresetDescriber


def _options():
    from randovania.interface_common.options import PerGameOptions
    return PerGameOptions


def _gui() -> game.GameGui:
    from randovania.games.metroid import gui

    return game.GameGui(
        game_tab=gui.MetroidGameTabWidget,
        tab_provider=gui.preset_tabs,
        cosmetic_dialog=gui.MetroidCosmeticPatchesDialog,
        export_dialog=gui.MetroidGameExportDialog,
        progressive_item_gui_tuples=(),
        spoiler_visualizer=(),
    )


def _generator() -> game.GameGenerator:
    from randovania.games.metroid import generator
    from randovania.generator.hint_distributor import AllJokesHintDistributor

    return game.GameGenerator(
        pickup_pool_creator=generator.pool_creator,
        bootstrap=generator.MetroidBootstrap(),
        base_patches_factory=generator.MetroidBasePatchesFactory(),
        hint_distributor=AllJokesHintDistributor(),
    )


def _patch_data_factory():
    from randovania.games.metroid.exporter.patch_data_factory import MetroidPatchDataFactory
    return MetroidPatchDataFactory


def _exporter():
    from randovania.games.metroid.exporter.game_exporter import MetroidGameExporter
    return MetroidGameExporter()


game_data: game.GameData = game.GameData(
    short_name="Metroid",
    long_name="Metroid",
    development_state=game.DevelopmentState.EXPERIMENTAL,

    presets=[
        {
            "path": "starter_preset.rdvpreset"
        },
    ],

    faq=[
        ("Which versions of Metroid Planets are supported?",
         "Only version 1.27g is supported. "
         "Later versions are embedding code in the executable"
         "which prevents from modifying the code.")
    ],

    layout=game.GameLayout(
        configuration=layout.MetroidConfiguration,
        cosmetic_patches=layout.MetroidCosmeticPatches,
        preset_describer=GamePresetDescriber(),
    ),

    options=_options,

    gui=_gui,

    generator=_generator,

    patch_data_factory=_patch_data_factory,

    exporter=_exporter,

    multiple_start_nodes_per_area=False,

    defaults_available_in_game_sessions=randovania.is_dev_version(),
)
