from __future__ import annotations

import typing

import randovania.game.data
import randovania.game.development_state
import randovania.game.game_test_data
import randovania.game.generator
import randovania.game.gui
import randovania.game.hints
import randovania.game.layout
import randovania.game.web_info
from randovania.games.yokus_island_express import layout

if typing.TYPE_CHECKING:
    from randovania.exporter.game_exporter import GameExporter
    from randovania.exporter.patch_data_factory import PatchDataFactory
    from randovania.interface_common.options import PerGameOptions


def _options() -> type[PerGameOptions]:
    from randovania.games.yokus_island_express.exporter.options import YokuPerGameOptions

    return YokuPerGameOptions


def _gui() -> randovania.game.gui.GameGui:
    from randovania.games.yokus_island_express import gui

    return randovania.game.gui.GameGui(
        game_tab=gui.YokuGameTabWidget,
        tab_provider=gui.preset_tabs,
        cosmetic_dialog=None,
        export_dialog=gui.YokuGameExportDialog,
        spoiler_visualizer=(),
    )


def _generator() -> randovania.game.generator.GameGenerator:
    from randovania.games.yokus_island_express import generator
    from randovania.generator.filler.weights import ActionWeights

    return randovania.game.generator.GameGenerator(
        pickup_pool_creator=generator.pool_creator,
        bootstrap=generator.YokuBootstrap(),
        base_patches_factory=generator.YokuBasePatchesFactory(),
        action_weights=ActionWeights(),
    )


def _hints() -> randovania.game.hints.GameHints:
    from randovania.generator.hint_distributor import AllJokesHintDistributor

    return randovania.game.hints.GameHints(
        hint_distributor=AllJokesHintDistributor(),
        specific_pickup_hints={},
    )


def _patch_data_factory() -> type[PatchDataFactory]:
    from randovania.games.yokus_island_express.exporter.patch_data_factory import YokuPatchDataFactory

    return YokuPatchDataFactory


def _exporter() -> GameExporter:
    from randovania.games.yokus_island_express.exporter.game_exporter import YokuGameExporter

    return YokuGameExporter()


def _hash_words() -> list[str]:
    from randovania.games.yokus_island_express.hash_words import HASH_WORDS

    return HASH_WORDS


def _test_data() -> randovania.game.game_test_data.GameTestData:
    return randovania.game.game_test_data.GameTestData(
        expected_seed_hash="U4K64HIE",
    )


game_data: randovania.game.data.GameData = randovania.game.data.GameData(
    short_name="Yoku",
    long_name="Yoku's Island Express",
    development_state=randovania.game.development_state.DevelopmentState.SOURCE_ONLY,
    presets=[
        "starter_preset.rdvpreset",
        "shuffled_trackers.rdvpreset",
    ],
    faq=[],
    web_info=randovania.game.web_info.GameWebInfo(
        what_can_randomize=(
            "The 248 locations of the game's own randomizer",
            "Abilities, keys, quest items, trackers, wallet upgrades, Wickerlings and fruit",
        ),
        need_to_play=("Yoku's Island Express for PC (GOG/Steam/Epic)",),
    ),
    hash_words=_hash_words(),
    layout=randovania.game.layout.GameLayout(
        configuration=layout.YokuConfiguration,
        cosmetic_patches=layout.YokuCosmeticPatches,
        preset_describer=layout.YokuPresetDescriber(),
    ),
    options=_options,
    gui=_gui,
    generator=_generator,
    hints=_hints,
    patch_data_factory=_patch_data_factory,
    exporter=_exporter,
    test_data=_test_data,
    reject_undocumented_tricks_in_database=True,
    multiple_start_nodes_per_area=True,
)
