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
        expected_seed_hash="TIPIPALP",
    )


# TODO
game_data: randovania.game.data.GameData = randovania.game.data.GameData(
    short_name="MZM",
    long_name="Metroid: Zero Mission",
    development_state=randovania.game.development_state.DevelopmentState.SOURCE_ONLY,
    presets=["starter_preset.rdvpreset"],
    faq=[
        (
            "Which versions of Zero Mission are supported?",
            "Only the USA version of Zero Mission is supported with no current plans to support additional versions.",
        ),
        (
            "I saved in a place I can't get out of, am I softlocked?",
            'You can use the "Warp to Start" function in the pause menu by pressing L and confirming. '
            "This will place you back at your start location with everything collected since your last save. "
            "Please note that this is never logical.",
        ),
        (
            "How do the Suit upgrades interact?",
            "Each suit collected provides additional reduction to enemy damage "
            "and provides unique resistances to environmental damage as described below.\n"
            "- Varia - provides immunity to Heat and Weak Acid, increased resistance to Lava and Strong Acid.\n"
            "- Gravity - provides increased resistance to all environmental types.\n"
            "- Both - provides immunity to Lava and additional resistance to Strong Acid.\n\n"
            "Gravity also provides free movement in all liquids.",
        ),
    ],
    web_info=randovania.game.web_info.GameWebInfo(
        what_can_randomize=(
            "All items",
            "Starting Locations",
        ),
        need_to_play=(
            "A ROM of Metroid Zero Mission (USA)",
            "A Gameboy Advance Emulator (recommended mGBA or Bizhawk)",
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
    multiple_start_nodes_per_area=True,
)
