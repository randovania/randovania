from __future__ import annotations

import randovania.game.data
import randovania.game.development_state
import randovania.game.generator
import randovania.game.gui
import randovania.game.layout
import randovania.game.web_info
from randovania.games.cave_story.layout.cs_configuration import CSConfiguration
from randovania.games.cave_story.layout.cs_cosmetic_patches import CSCosmeticPatches
from randovania.games.cave_story.layout.preset_describer import (
    CSPresetDescriber,
    get_ingame_hash_str,
)


def _options():
    from randovania.games.cave_story.exporter.options import CSPerGameOptions

    return CSPerGameOptions


def _gui():
    from randovania.games.cave_story import gui
    from randovania.games.cave_story.layout import progressive_items

    return randovania.game.gui.GameGui(
        tab_provider=gui.cs_preset_tabs,
        cosmetic_dialog=gui.CSCosmeticPatchesDialog,
        export_dialog=gui.CSGameExportDialog,
        progressive_item_gui_tuples=progressive_items.tuples(),
        spoiler_visualizer=(gui.CSHintDetailsTab,),
        game_tab=gui.CSGameTabWidget,
    )


def _generator():
    from randovania.games.cave_story.generator.bootstrap import CSBootstrap
    from randovania.games.cave_story.generator.hint_distributor import CSHintDistributor
    from randovania.games.cave_story.generator.pool_creator import pool_creator
    from randovania.generator.base_patches_factory import BasePatchesFactory
    from randovania.generator.filler.weights import ActionWeights

    return randovania.game.generator.GameGenerator(
        pickup_pool_creator=pool_creator,
        bootstrap=CSBootstrap(),
        base_patches_factory=BasePatchesFactory(),
        hint_distributor=CSHintDistributor(),
        action_weights=ActionWeights(),
    )


def _patch_data_factory():
    from randovania.games.cave_story.exporter.patch_data_factory import CSPatchDataFactory

    return CSPatchDataFactory


def _exporter():
    from randovania.games.cave_story.exporter.game_exporter import CSGameExporter

    return CSGameExporter()


def _hash_words() -> list[str]:
    from randovania.games.cave_story.hash_words import HASH_WORDS

    return HASH_WORDS


game_data: randovania.game.data.GameData = randovania.game.data.GameData(
    short_name="CS",
    long_name="Cave Story",
    development_state=randovania.game.development_state.DevelopmentState.STABLE,
    presets=[
        {"path": "starter_preset.rdvpreset"},
        {"path": "multiworld-starter-preset.rdvpreset"},
        {"path": "classic.rdvpreset"},
    ],
    faq=[],
    web_info=randovania.game.web_info.GameWebInfo(
        what_can_randomize=[
            "All items",
            "Starting locations",
        ],
        need_to_play=[
            (
                "The game is included with Randovania. Windows or Wine is needed to play Freeware."
                "Windows or Linux is needed to play Cave Story Tweaked"
            ),
        ],
    ),
    hash_words=_hash_words(),
    layout=randovania.game.layout.GameLayout(
        configuration=CSConfiguration,
        cosmetic_patches=CSCosmeticPatches,
        preset_describer=CSPresetDescriber(),
        get_ingame_hash=get_ingame_hash_str,
    ),
    options=_options,
    gui=_gui,
    generator=_generator,
    patch_data_factory=_patch_data_factory,
    exporter=_exporter,
    defaults_available_in_game_sessions=True,
)
