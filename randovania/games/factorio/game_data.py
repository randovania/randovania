from __future__ import annotations

import typing

import randovania.game.data
import randovania.game.development_state
import randovania.game.generator
import randovania.game.gui
import randovania.game.layout
from randovania.games.factorio import layout

if typing.TYPE_CHECKING:
    from randovania.exporter.game_exporter import GameExporter
    from randovania.exporter.patch_data_factory import PatchDataFactory
    from randovania.interface_common.options import PerGameOptions


def _options() -> type[PerGameOptions]:
    from randovania.games.factorio.exporter.options import FactorioPerGameOptions

    return FactorioPerGameOptions


def _gui() -> randovania.game.gui.GameGui:
    from randovania.games.factorio import gui

    return randovania.game.gui.GameGui(
        game_tab=gui.FactorioGameTabWidget,
        tab_provider=gui.preset_tabs,
        cosmetic_dialog=None,
        export_dialog=gui.FactorioGameExportDialog,
        progressive_item_gui_tuples=(),
        spoiler_visualizer=(),
    )


def _generator() -> randovania.game.generator.GameGenerator:
    from randovania.games.factorio import generator
    from randovania.generator.filler.weights import ActionWeights
    from randovania.generator.hint_distributor import AllJokesHintDistributor

    return randovania.game.generator.GameGenerator(
        pickup_pool_creator=generator.pool_creator,
        bootstrap=generator.FactorioBootstrap(),
        base_patches_factory=generator.FactorioBasePatchesFactory(),
        hint_distributor=AllJokesHintDistributor(),
        action_weights=ActionWeights(),
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


game_data: randovania.game.data.GameData = randovania.game.data.GameData(
    short_name="Factorio",
    long_name="Factorio",
    development_state=randovania.game.development_state.DevelopmentState.EXPERIMENTAL,
    presets=[
        {"path": "starter_preset.rdvpreset"},
    ],
    faq=[
        ("What versions of the game is supported?", "Only Factorio 2.0 is supported."),
        ("Is Factorio: Space Age supported?", "No."),
        ("Are other mods supported?", "Only mods that don't add new researches are compatible."),
        (
            "Is multiplayer supported?",
            "Yes. Since the generated randomizer mod file isn't in the mod portal, "
            "it'll be necessary to either share the mod file or have everyone export it themselves.",
        ),
    ],
    web_info=randovania.game.web_info.GameWebInfo(
        what_can_randomize=[
            "The tech tree",
            "The recipes for all Science Packs",
            "The recipes for rocket parts",
        ],
        need_to_play=[
            "A copy of the game from Steam or Factorio.com",
        ],
    ),
    hash_words=_hash_words(),
    layout=randovania.game.layout.GameLayout(
        configuration=layout.FactorioConfiguration,
        cosmetic_patches=layout.FactorioCosmeticPatches,
        preset_describer=layout.FactorioPresetDescriber(),
    ),
    options=_options,
    gui=_gui,
    generator=_generator,
    patch_data_factory=_patch_data_factory,
    exporter=_exporter,
    multiple_start_nodes_per_area=True,
)
