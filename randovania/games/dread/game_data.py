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
    )


def _patch_data_factory():
    from randovania.games.dread.exporter.patch_data_factory import DreadPatchDataFactory
    return DreadPatchDataFactory


def _exporter():
    from randovania.games.dread.exporter.game_exporter import DreadGameExporter
    return DreadGameExporter()


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


game_data: game.GameData = game.GameData(
    short_name="Dread",
    long_name="Metroid Dread",
    development_state=game.DevelopmentState.EXPERIMENTAL,

    presets=[
        {
            "path": "starter_preset.rdvpreset"
        }
    ],

    faq=[],

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
