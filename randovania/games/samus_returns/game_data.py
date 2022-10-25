from randovania.games import game
from randovania.games.samus_returns.layout.samus_returns_configuration import SRConfiguration
from randovania.games.samus_returns.layout.samus_returns_cosmetic_patches import SRCosmeticPatches
from randovania.layout.preset_describer import GamePresetDescriber


def _options():
    from randovania.interface_common.options import PerGameOptions
    return PerGameOptions


def _gui() -> game.GameGui:
    from randovania.games.samus_returns import gui

    return game.GameGui(
        game_tab=gui.SRGameTabWidget,
        tab_provider=gui.preset_tabs,
        cosmetic_dialog=gui.SRCosmeticPatchesDialog,
        export_dialog=gui.SRGameExportDialog,
        progressive_item_gui_tuples=tuple(),
        spoiler_visualizer=tuple(),
    )


def _generator() -> game.GameGenerator:
    from randovania.games.samus_returns import generator
    from randovania.generator.hint_distributor import AllJokesHintDistributor

    return game.GameGenerator(
        item_pool_creator=generator.pool_creator,
        bootstrap=generator.SRBootstrap(),
        base_patches_factory=generator.SRBasePatchesFactory(),
        hint_distributor=AllJokesHintDistributor(),
    )


def _patch_data_factory():
    from randovania.games.samus_returns.exporter.patch_data_factory import SRPatchDataFactory
    return SRPatchDataFactory


def _exporter():
    from randovania.games.samus_returns.exporter.game_exporter import SRGameExporter
    return SRGameExporter()

game_data: game.GameData = game.GameData(
    short_name="SR",
    long_name="Metroid: Samus Returns",
    development_state=game.DevelopmentState.EXPERIMENTAL,

    presets=[
        {
            "path": "starter_preset.rdvpreset"
        }
    ],

    faq=[],

    layout=game.GameLayout(
        configuration=SRConfiguration,
        cosmetic_patches=SRCosmeticPatches,
        preset_describer=GamePresetDescriber()
    ),

    options=_options,

    gui=_gui,

    generator=_generator,

    patch_data_factory=_patch_data_factory,

    exporter=_exporter,
)