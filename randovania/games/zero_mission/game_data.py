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
from randovania.games.zero_mission import layout
from randovania.layout.preset_describer import GamePresetDescriber

if typing.TYPE_CHECKING:
    from randovania.exporter.game_exporter import GameExporter
    from randovania.exporter.patch_data_factory import PatchDataFactory
    from randovania.interface_common.options import PerGameOptions


def _options() -> type[PerGameOptions]:
    from randovania.games.zero_mission.exporter.options import MZMPerGameOptions

    return MZMPerGameOptions


def _gui() -> randovania.game.gui.GameGui:
    from randovania.games.zero_mission import gui
    from randovania.games.zero_mission.layout import progressive_items
    from randovania.gui.game_details.hint_details_tab import HintDetailsTab

    return randovania.game.gui.GameGui(
        game_tab=gui.MZMGameTabWidget,
        tab_provider=gui.preset_tabs,
        cosmetic_dialog=gui.MZMCosmeticPatchesDialog,
        export_dialog=gui.MZMGameExportDialog,
        progressive_item_gui_tuples=progressive_items.tuples(),
        spoiler_visualizer=(HintDetailsTab,),
    )


def _generator() -> randovania.game.generator.GameGenerator:
    from randovania.games.zero_mission import generator
    from randovania.generator.filler.weights import ActionWeights

    return randovania.game.generator.GameGenerator(
        pickup_pool_creator=generator.pool_creator,
        bootstrap=generator.MZMBootstrap(),
        base_patches_factory=generator.MZMBasePatchesFactory(),
        action_weights=ActionWeights(),
    )


def _hints() -> randovania.game.hints.GameHints:
    from randovania.games.zero_mission import generator

    return randovania.game.hints.GameHints(
        hint_distributor=generator.MZMHintDistributor(),
        specific_pickup_hints={},
    )


def _patch_data_factory() -> type[PatchDataFactory]:
    from randovania.games.zero_mission.exporter.patch_data_factory import MZMPatchDataFactory

    return MZMPatchDataFactory


def _exporter() -> GameExporter:
    from randovania.games.zero_mission.exporter.game_exporter import MZMGameExporter

    return MZMGameExporter()


def _hash_words() -> list[str]:
    from randovania.games.zero_mission.hash_words import HASH_WORDS

    return HASH_WORDS


def _test_data() -> randovania.game.game_test_data.GameTestData:
    return randovania.game.game_test_data.GameTestData(
        expected_seed_hash="JF3VKSGV",
    )


# TODO
game_data: randovania.game.data.GameData = randovania.game.data.GameData(
    short_name="MZM",
    long_name="Metroid: Zero Mission",
    development_state=randovania.game.development_state.DevelopmentState.SOURCE_ONLY,
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
        configuration=layout.MZMConfiguration,
        cosmetic_patches=layout.MZMCosmeticPatches,
        preset_describer=GamePresetDescriber(),
    ),
    options=_options,
    gui=_gui,
    generator=_generator,
    hints=_hints,
    patch_data_factory=_patch_data_factory,
    exporter=_exporter,
    test_data=_test_data,
    reject_undocumented_tricks_in_database=False,
    multiple_start_nodes_per_area=True,
)
