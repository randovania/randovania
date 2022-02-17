from randovania.games import game
from randovania.games.dread.layout.dread_configuration import DreadConfiguration
from randovania.games.dread.layout.dread_cosmetic_patches import DreadCosmeticPatches
from randovania.games.dread.layout.preset_describer import (
    dread_format_params, dread_expected_items,
    dread_unexpected_items
)
from randovania.games.dread.patcher.open_dread_patcher import OpenDreadPatcher
from randovania.games.game import GameData, GameLayout, GamePresetDescriber


def _gui() -> game.GameGui:
    from randovania.games.dread.gui.dialog.dread_cosmetic_patches_dialog import DreadCosmeticPatchesDialog
    from randovania.games.dread.gui.preset_settings import dread_preset_tabs
    from randovania.games.dread.item_database import progressive_items
    from randovania.games.prime2.gui.hint_details_tab import EchoesHintDetailsTab

    return game.GameGui(
        tab_provider=dread_preset_tabs,
        cosmetic_dialog=DreadCosmeticPatchesDialog,
        input_file_text=("an extracted RomFS folder", "the Nintendo Switch", "RomFS folder"),
        progressive_item_gui_tuples=progressive_items.gui_tuples(),
        spoiler_visualizer=(EchoesHintDetailsTab,),
    )


def _generator() -> game.GameGenerator:
    from randovania.games.dread.generator.base_patches_factory import DreadBasePatchesFactory
    from randovania.games.dread.generator.pool_creator import pool_creator
    from randovania.resolver.bootstrap import MetroidBootstrap
    from randovania.games.dread.generator.hint_distributor import DreadHintDistributor

    return game.GameGenerator(
        item_pool_creator=pool_creator,
        base_patches_factory=DreadBasePatchesFactory(),
        bootstrap=MetroidBootstrap(),
        hint_distributor=DreadHintDistributor(),
    )


game_data: GameData = GameData(
    short_name="Dread",
    long_name="Metroid Dread",
    experimental=True,

    presets=[
        {
            "path": "starter_preset.rdvpreset"
        }
    ],

    faq=[],

    layout=GameLayout(
        configuration=DreadConfiguration,
        cosmetic_patches=DreadCosmeticPatches,
        preset_describer=GamePresetDescriber(
            expected_items=dread_expected_items,
            unexpected_items=dread_unexpected_items,
            format_params=dread_format_params,
        )
    ),

    gui=_gui,

    generator=_generator,

    patcher=OpenDreadPatcher(),
)
