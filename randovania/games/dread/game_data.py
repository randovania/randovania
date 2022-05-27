from randovania.games import game
from randovania.games.dread.layout.dread_configuration import DreadConfiguration
from randovania.games.dread.layout.dread_cosmetic_patches import DreadCosmeticPatches
from randovania.games.dread.layout.preset_describer import (
    DreadPresetDescriber
)


def _options():
    from randovania.games.dread.exporter.options import DreadPerGameOptions
    return DreadPerGameOptions


def _gui() -> game.GameGui:
    from randovania.games.dread import gui
    from randovania.games.dread.item_database import progressive_items

    return game.GameGui(
        tab_provider=gui.dread_preset_tabs,
        cosmetic_dialog=gui.DreadCosmeticPatchesDialog,
        export_dialog=gui.DreadGameExportDialog,
        progressive_item_gui_tuples=progressive_items.tuples(),
        spoiler_visualizer=(gui.DreadHintDetailsTab,),
        help_widget=lambda: gui.DreadHelpWidget(),
    )


def _patch_data_factory():
    from randovania.games.dread.exporter.patch_data_factory import DreadPatchDataFactory
    return DreadPatchDataFactory


def _exporter():
    from randovania.games.dread.exporter.game_exporter import DreadGameExporter
    return DreadGameExporter()


def _generator() -> game.GameGenerator:
    from randovania.games.dread.generator.base_patches_factory import DreadBasePatchesFactory
    from randovania.games.dread.generator.bootstrap import DreadBootstrap
    from randovania.games.dread.generator.pool_creator import pool_creator
    from randovania.games.dread.generator.hint_distributor import DreadHintDistributor

    return game.GameGenerator(
        item_pool_creator=pool_creator,
        base_patches_factory=DreadBasePatchesFactory(),
        bootstrap=DreadBootstrap(),
        hint_distributor=DreadHintDistributor(),
    )


game_data: game.GameData = game.GameData(
    short_name="Dread",
    long_name="Metroid Dread",
    development_state=game.DevelopmentState.DEVELOPMENT,

    presets=[
        {
            "path": "starter_preset.rdvpreset"
        }
    ],

    faq=[
        (
            "Why does this missile door doesn't open after I shoot a missile at it?",
            "Shoot another missile at the door. In the process of making certain missile doors possible to open from "
            "both sides, this issue shows up."
        ),
        (
            "Using an Energy Recharge Station heals me to 299, but my energy maximum is 249. Which one is correct?",
            "The 299 is a display error. You can always see the correct value in the inventory screen."
        )
    ],

    layout=game.GameLayout(
        configuration=DreadConfiguration,
        cosmetic_patches=DreadCosmeticPatches,
        preset_describer=DreadPresetDescriber()
    ),

    options=_options,

    gui=_gui,

    generator=_generator,

    patch_data_factory=_patch_data_factory,

    exporter=_exporter,
)
