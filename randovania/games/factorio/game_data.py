from __future__ import annotations

import typing

from randovania.games import game
from randovania.games.factorio import layout
from randovania.layout.preset_describer import GamePresetDescriber

if typing.TYPE_CHECKING:
    from randovania.exporter.game_exporter import GameExporter
    from randovania.exporter.patch_data_factory import PatchDataFactory
    from randovania.interface_common.options import PerGameOptions


def _options() -> type[PerGameOptions]:
    from randovania.games.factorio.exporter.options import FactorioPerGameOptions

    return FactorioPerGameOptions


def _gui() -> game.GameGui:
    from randovania.games.factorio import gui

    return game.GameGui(
        game_tab=gui.FactorioGameTabWidget,
        tab_provider=gui.preset_tabs,
        cosmetic_dialog=None,
        export_dialog=gui.FactorioGameExportDialog,
        progressive_item_gui_tuples=(),
        spoiler_visualizer=(),
    )


def _generator() -> game.GameGenerator:
    from randovania.games.factorio import generator
    from randovania.generator.hint_distributor import AllJokesHintDistributor

    return game.GameGenerator(
        pickup_pool_creator=generator.pool_creator,
        bootstrap=generator.FactorioBootstrap(),
        base_patches_factory=generator.FactorioBasePatchesFactory(),
        hint_distributor=AllJokesHintDistributor(),
    )


def _patch_data_factory() -> type[PatchDataFactory]:
    from randovania.games.factorio.exporter.patch_data_factory import FactorioPatchDataFactory

    return FactorioPatchDataFactory


def _exporter() -> GameExporter:
    from randovania.games.factorio.exporter.game_exporter import FactorioGameExporter

    return FactorioGameExporter()


def _hash_words() -> list[str]:
    from randovania.games.factorio.hash_words import HASH_WORDS

    return HASH_WORDS


game_data: game.GameData = game.GameData(
    short_name="Factorio",
    long_name="Factorio",
    development_state=game.DevelopmentState.EXPERIMENTAL,
    presets=[
        {"path": "starter_preset.rdvpreset"},
    ],
    faq=[],
    hash_words=_hash_words(),
    layout=game.GameLayout(
        configuration=layout.FactorioConfiguration,
        cosmetic_patches=layout.FactorioCosmeticPatches,
        preset_describer=GamePresetDescriber(),
    ),
    options=_options,
    gui=_gui,
    generator=_generator,
    patch_data_factory=_patch_data_factory,
    exporter=_exporter,
    multiple_start_nodes_per_area=True,
)
