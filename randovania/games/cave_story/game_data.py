from randovania.games.cave_story.layout.cs_configuration import CSConfiguration
from randovania.games.cave_story.layout.cs_cosmetic_patches import CSCosmeticPatches
from randovania.games.cave_story.layout.preset_describer import (
    cs_format_params, cs_expected_items,
    cs_unexpected_items, get_ingame_hash_str,
)
from randovania.games.cave_story.patcher.caver_patcher import CaverPatcher
from randovania.games.game import GameData, GameGenerator, GameGui, GameLayout, GamePresetDescriber


def _gui():
    from randovania.games.cave_story.gui.hint_details_tab import HintDetailsTab
    from randovania.games.cave_story.gui.dialog.cs_cosmetic_patches_dialog import CSCosmeticPatchesDialog
    from randovania.games.cave_story.gui.preset_settings import cs_preset_tabs
    from randovania.games.cave_story.gui.cs_help_widget import CSHelpWidget
    from randovania.games.cave_story.item_database import progressive_items

    return GameGui(
        tab_provider=cs_preset_tabs,
        cosmetic_dialog=CSCosmeticPatchesDialog,
        progressive_item_gui_tuples=progressive_items.gui_tuples(),
        spoiler_visualizer=(HintDetailsTab,),
        help_widget=lambda: CSHelpWidget(),
    )


def _generator():
    from randovania.games.cave_story.generator.base_patches_factory import CSBasePatchesFactory
    from randovania.games.cave_story.generator.bootstrap import CSBootstrap
    from randovania.games.cave_story.generator.hint_distributor import CSHintDistributor
    from randovania.games.cave_story.generator.pool_creator import pool_creator

    return GameGenerator(
        item_pool_creator=pool_creator,
        bootstrap=CSBootstrap(),
        base_patches_factory=CSBasePatchesFactory(),
        hint_distributor=CSHintDistributor(),
    )


game_data: GameData = GameData(
    short_name="CS",
    long_name="Cave Story",
    experimental=False,

    presets=[
        {
            "path": "starter_preset.rdvpreset"
        },
        {
            "path": "classic.rdvpreset"
        }
    ],

    faq=[],

    layout=GameLayout(
        configuration=CSConfiguration,
        cosmetic_patches=CSCosmeticPatches,
        preset_describer=GamePresetDescriber(
            expected_items=cs_expected_items,
            unexpected_items=cs_unexpected_items,
            format_params=cs_format_params,
        ),
        get_ingame_hash=get_ingame_hash_str,
    ),

    gui=_gui,

    generator=_generator,

    patcher=CaverPatcher()
)
