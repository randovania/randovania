from __future__ import annotations

import typing

import randovania
from randovania.games import game
from randovania.games.blank import layout
from randovania.layout.preset_describer import GamePresetDescriber

if typing.TYPE_CHECKING:
    from randovania.exporter.game_exporter import GameExporter
    from randovania.exporter.patch_data_factory import PatchDataFactory
    from randovania.interface_common.options import PerGameOptions


def _options() -> type[PerGameOptions]:
    from randovania.games.blank.exporter.options import BlankPerGameOptions

    return BlankPerGameOptions


def _gui() -> game.GameGui:
    from randovania.games.blank import gui

    return game.GameGui(
        game_tab=gui.BlankGameTabWidget,
        tab_provider=gui.preset_tabs,
        cosmetic_dialog=gui.BlankCosmeticPatchesDialog,
        export_dialog=gui.BlankGameExportDialog,
        progressive_item_gui_tuples=(),
        spoiler_visualizer=(),
    )


def _generator() -> game.GameGenerator:
    from randovania.games.blank import generator
    from randovania.generator.hint_distributor import AllJokesHintDistributor

    return game.GameGenerator(
        pickup_pool_creator=generator.pool_creator,
        bootstrap=generator.BlankBootstrap(),
        base_patches_factory=generator.BlankBasePatchesFactory(),
        hint_distributor=AllJokesHintDistributor(),
    )


def _patch_data_factory() -> type[PatchDataFactory]:
    from randovania.games.blank.exporter.patch_data_factory import BlankPatchDataFactory

    return BlankPatchDataFactory


def _exporter() -> GameExporter:
    from randovania.games.blank.exporter.game_exporter import BlankGameExporter

    return BlankGameExporter()


game_data: game.GameData = game.GameData(
    short_name="Blank",
    long_name="Blank Development Game",
    development_state=game.DevelopmentState.EXPERIMENTAL,
    presets=[
        {"path": "starter_preset.rdvpreset"},
    ],
    faq=[],
    web_info=game.GameWebInfo(
        what_can_randomize=(
            "Everything",
            "Nothing",
        ),
        need_to_play=(
            "A Nintendo Virtual Boy",
            "Your original Virtual Boy Game Cartridge",
        ),
    ),
    layout=game.GameLayout(
        configuration=layout.BlankConfiguration,
        cosmetic_patches=layout.BlankCosmeticPatches,
        preset_describer=GamePresetDescriber(),
    ),
    options=_options,
    gui=_gui,
    generator=_generator,
    patch_data_factory=_patch_data_factory,
    exporter=_exporter,
    multiple_start_nodes_per_area=True,
    defaults_available_in_game_sessions=randovania.is_dev_version(),
)
