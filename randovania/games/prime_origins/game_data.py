from __future__ import annotations

import typing

import randovania
import randovania.game.data
import randovania.game.development_state
import randovania.game.game_test_data
import randovania.game.generator
import randovania.game.gui
import randovania.game.hints
import randovania.game.layout
import randovania.game.web_info
from randovania.games.prime_origins import layout
from randovania.layout.preset_describer import GamePresetDescriber

if typing.TYPE_CHECKING:
    from randovania.exporter.game_exporter import GameExporter
    from randovania.exporter.patch_data_factory import PatchDataFactory
    from randovania.interface_common.options import PerGameOptions


def _options() -> type[PerGameOptions]:
    from randovania.games.prime_origins.exporter.options import MPOPerGameOptions

    return MPOPerGameOptions


def _gui() -> randovania.game.gui.GameGui:
    from randovania.games.prime_origins import gui
    from randovania.games.prime_origins.layout import progressive_items
    from randovania.gui.game_details.hint_details_tab import HintDetailsTab

    return randovania.game.gui.GameGui(
        game_tab=gui.MPOGameTabWidget,
        tab_provider=gui.preset_tabs,
        cosmetic_dialog=gui.MPOCosmeticPatchesDialog,
        export_dialog=gui.MPOGameExportDialog,
        progressive_item_gui_tuples=progressive_items.tuples(),
        spoiler_visualizer=(HintDetailsTab,),
    )


def _generator() -> randovania.game.generator.GameGenerator:
    from randovania.games.prime_origins import generator
    from randovania.generator.filler.weights import ActionWeights

    return randovania.game.generator.GameGenerator(
        pickup_pool_creator=generator.pool_creator,
        bootstrap=generator.MPOBootstrap(),
        base_patches_factory=generator.MPOBasePatchesFactory(),
        action_weights=ActionWeights(),
    )


def _hints() -> randovania.game.hints.GameHints:
    from randovania.games.prime_origins import generator

    return randovania.game.hints.GameHints(
        hint_distributor=generator.MPOHintDistributor(),
        specific_pickup_hints={
            "victory_key": randovania.game.hints.SpecificHintDetails(
                long_name="Victory Key",
                description="This controls how precise the hint for the Victory Key is.",
            )
        },
    )


def _patch_data_factory() -> type[PatchDataFactory]:
    from randovania.games.prime_origins.exporter.patch_data_factory import MPOPatchDataFactory

    return MPOPatchDataFactory


def _exporter() -> GameExporter:
    from randovania.games.prime_origins.exporter.game_exporter import MPOGameExporter

    return MPOGameExporter()


def _hash_words() -> list[str]:
    from randovania.games.prime_origins.hash_words import HASH_WORDS

    return HASH_WORDS


def _test_data() -> randovania.game.game_test_data.GameTestData:
    return randovania.game.game_test_data.GameTestData(
        expected_seed_hash="AFINWQGP",
    )


game_data: randovania.game.data.GameData = randovania.game.data.GameData(
    short_name="MPO",
    long_name="Metroid Prime Origins",
    development_state=randovania.game.development_state.DevelopmentState.STAGING,
    presets=["starter_preset.rdvpreset"],
    faq=[],
    web_info=randovania.game.web_info.GameWebInfo(
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
    layout=randovania.game.layout.GameLayout(
        configuration=layout.MPOConfiguration,
        cosmetic_patches=layout.MPOCosmeticPatches,
        preset_describer=GamePresetDescriber(),
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
