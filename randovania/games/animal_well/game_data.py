from __future__ import annotations

import typing

from randovania.games import game
from randovania.games.animal_well import layout
from randovania.layout.preset_describer import GamePresetDescriber

if typing.TYPE_CHECKING:
    from randovania.exporter.game_exporter import GameExporter
    from randovania.exporter.patch_data_factory import PatchDataFactory
    from randovania.interface_common.options import PerGameOptions


def _options() -> type[PerGameOptions]:
    from randovania.games.animal_well.exporter.options import AWPerGameOptions

    return AWPerGameOptions


def _gui() -> game.GameGui:
    from randovania.games.animal_well import gui

    return game.GameGui(
        game_tab=gui.AWGameTabWidget,
        tab_provider=gui.preset_tabs,
        cosmetic_dialog=gui.AWCosmeticPatchesDialog,
        export_dialog=gui.AWGameExportDialog,
        progressive_item_gui_tuples=(),
        spoiler_visualizer=(),
    )


def _generator() -> game.GameGenerator:
    from randovania.games.animal_well import generator
    from randovania.generator.hint_distributor import AllJokesHintDistributor

    return game.GameGenerator(
        pickup_pool_creator=generator.pool_creator,
        bootstrap=generator.AWBootstrap(),
        base_patches_factory=generator.AWBasePatchesFactory(),
        hint_distributor=AllJokesHintDistributor(),
    )


def _patch_data_factory() -> type[PatchDataFactory]:
    from randovania.games.animal_well.exporter.patch_data_factory import AWPatchDataFactory

    return AWPatchDataFactory


def _exporter() -> GameExporter:
    from randovania.games.animal_well.exporter.game_exporter import AWGameExporter

    return AWGameExporter()


def _hash_words() -> list[str]:
    from randovania.games.animal_well.hash_words import HASH_WORDS

    return HASH_WORDS


game_data: game.GameData = game.GameData(
    short_name="AW",
    long_name="Animal Well",
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
    hash_words=_hash_words(),
    layout=game.GameLayout(
        configuration=layout.AWConfiguration,
        cosmetic_patches=layout.AWCosmeticPatches,
        preset_describer=GamePresetDescriber(),
    ),
    options=_options,
    gui=_gui,
    generator=_generator,
    patch_data_factory=_patch_data_factory,
    exporter=_exporter,
    multiple_start_nodes_per_area=True,
)
