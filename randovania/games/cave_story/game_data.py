from __future__ import annotations

from randovania.games import game
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
    from randovania.games.cave_story.pickup_database import progressive_items

    return game.GameGui(
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

    return game.GameGenerator(
        pickup_pool_creator=pool_creator,
        bootstrap=CSBootstrap(),
        base_patches_factory=BasePatchesFactory(),
        hint_distributor=CSHintDistributor(),
    )


def _patch_data_factory():
    from randovania.games.cave_story.exporter.patch_data_factory import CSPatchDataFactory

    return CSPatchDataFactory


def _exporter():
    from randovania.games.cave_story.exporter.game_exporter import CSGameExporter

    return CSGameExporter()


game_data: game.GameData = game.GameData(
    short_name="CS",
    long_name="Cave Story",
    development_state=game.DevelopmentState.STABLE,
    presets=[
        {"path": "starter_preset.rdvpreset"},
        {"path": "multiworld-starter-preset.rdvpreset"},
        {"path": "classic.rdvpreset"},
    ],
    faq=[],
    web_info=game.GameWebInfo(
        what_can_randomize=[
            "All items",
            "Starting locations",
        ],
        need_to_play=[
            "Windows, Linux, or Wine. The game is included with Randovania",
        ],
    ),
    layout=game.GameLayout(
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
