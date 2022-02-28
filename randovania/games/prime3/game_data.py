from randovania.games import game
from randovania.games.prime3.layout.corruption_configuration import CorruptionConfiguration
from randovania.games.prime3.layout.corruption_cosmetic_patches import CorruptionCosmeticPatches
from randovania.games.prime3.layout.preset_describer import (
    CorruptionPresetDescriber
)


def _options():
    from randovania.interface_common.options import PerGameOptions
    return PerGameOptions


def _gui() -> game.GameGui:
    from randovania.games.prime3.item_database import progressive_items
    from randovania.games.prime3 import gui

    return game.GameGui(
        tab_provider=gui.prime3_preset_tabs,
        cosmetic_dialog=gui.CorruptionCosmeticPatchesDialog,
        export_dialog=gui.CorruptionGameExportDialog,
        progressive_item_gui_tuples=progressive_items.tuples(),
        help_widget=lambda: gui.CorruptionHelpWidget(),
    )


def _generator() -> game.GameGenerator:
    from randovania.games.prime3.generator.item_pool.pool_creator import corruption_specific_pool
    from randovania.generator.base_patches_factory import PrimeTrilogyBasePatchesFactory
    from randovania.generator.hint_distributor import AllJokesHintDistributor
    from randovania.resolver.bootstrap import MetroidBootstrap

    return game.GameGenerator(
        item_pool_creator=corruption_specific_pool,
        bootstrap=MetroidBootstrap(),
        base_patches_factory=PrimeTrilogyBasePatchesFactory(),
        hint_distributor=AllJokesHintDistributor(),
    )


def _patch_data_factory():
    from randovania.games.prime3.exporter.patch_data_factory import CorruptionPatchDataFactory
    return CorruptionPatchDataFactory


def _exporter():
    from randovania.games.prime3.exporter.game_exporter import CorruptionGameExporter
    return CorruptionGameExporter()


game_data: game.GameData = game.GameData(
    short_name="Corruption",
    long_name="Metroid Prime 3: Corruption",
    development_state=game.DevelopmentState.EXPERIMENTAL,

    presets=[
        {
            "path": "starter_preset.rdvpreset"
        }
    ],

    faq=[],

    layout=game.GameLayout(
        configuration=CorruptionConfiguration,
        cosmetic_patches=CorruptionCosmeticPatches,
        preset_describer=CorruptionPresetDescriber(),
    ),

    options=_options,

    gui=_gui,

    generator=_generator,

    patch_data_factory=_patch_data_factory,

    exporter=_exporter,
)
