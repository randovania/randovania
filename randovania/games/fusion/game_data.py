from __future__ import annotations

import typing

from randovania.games import game
from randovania.games.fusion import layout
from randovania.games.fusion.layout.preset_describer import FusionPresetDescriber

if typing.TYPE_CHECKING:
    from randovania.exporter.game_exporter import GameExporter
    from randovania.exporter.patch_data_factory import PatchDataFactory
    from randovania.interface_common.options import PerGameOptions


def _options() -> type[PerGameOptions]:
    from randovania.games.fusion.exporter.options import FusionPerGameOptions

    return FusionPerGameOptions


def _gui() -> game.GameGui:
    from randovania.games.fusion import gui

    return game.GameGui(
        game_tab=gui.FusionGameTabWidget,
        tab_provider=gui.preset_tabs,
        cosmetic_dialog=gui.FusionCosmeticPatchesDialog,
        export_dialog=gui.FusionGameExportDialog,
        progressive_item_gui_tuples=(),
        spoiler_visualizer=(),
    )


def _generator() -> game.GameGenerator:
    from randovania.games.fusion import generator
    from randovania.generator.hint_distributor import AllJokesHintDistributor

    return game.GameGenerator(
        pickup_pool_creator=generator.pool_creator,
        bootstrap=generator.FusionBootstrap(),
        base_patches_factory=generator.FusionBasePatchesFactory(),
        hint_distributor=AllJokesHintDistributor(),
    )


def _patch_data_factory() -> type[PatchDataFactory]:
    from randovania.games.fusion.exporter.patch_data_factory import FusionPatchDataFactory

    return FusionPatchDataFactory


def _exporter() -> GameExporter:
    from randovania.games.fusion.exporter.game_exporter import FusionGameExporter

    return FusionGameExporter()


game_data: game.GameData = game.GameData(
    short_name="Fusion",
    long_name="Metroid Fusion",
    development_state=game.DevelopmentState.EXPERIMENTAL,
    presets=[
        {"path": "starter_preset.rdvpreset"},
    ],
    faq=[
        (
            "What patcher does Randovania use?",
            "Randovania supports the open source patcher MARS (Metroid Advance Randomizer System). "
            "This is a new patcher built from scratch and is unrelated to other Fusion Randomizers. "
            "Any differences from the vanilla game are covered under the differences tab.",
        ),
        (
            "Which versions of Fusion are supported?",
            "Only the USA version of Fusion is supported with no current plans to support additional versions.",
        ),
        (
            "I saved in a place I can't get out of, am I softlocked?",
            'You can use the "Warp to Start" function in the pause menu by pressing L and confirming. '
            "This will place you back at your start location with everything collected since your last save. "
            "Please note that this is never logical.",
        ),
    ],
    layout=game.GameLayout(
        configuration=layout.FusionConfiguration,
        cosmetic_patches=layout.FusionCosmeticPatches,
        preset_describer=FusionPresetDescriber(),
    ),
    options=_options,
    gui=_gui,
    generator=_generator,
    patch_data_factory=_patch_data_factory,
    exporter=_exporter,
    multiple_start_nodes_per_area=True,
)
