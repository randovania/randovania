from randovania.games import game
from randovania.games.blank import layout
from randovania.layout.preset_describer import GamePresetDescriber


def _options():
    from randovania.interface_common.options import PerGameOptions
    return PerGameOptions


def _gui() -> game.GameGui:
    from randovania.games.blank import gui

    return game.GameGui(
        tab_provider=gui.preset_tabs,
        cosmetic_dialog=gui.BlankCosmeticPatchesDialog,
        export_dialog=gui.BlankGameExportDialog,
        progressive_item_gui_tuples=tuple(),
        spoiler_visualizer=tuple(),
    )


def _generator() -> game.GameGenerator:
    from randovania.games.blank import generator
    from randovania.generator.hint_distributor import AllJokesHintDistributor

    return game.GameGenerator(
        item_pool_creator=generator.pool_creator,
        bootstrap=generator.BlankBootstrap(),
        base_patches_factory=generator.BlankBasePatchesFactory(),
        hint_distributor=AllJokesHintDistributor(),
    )


def _patch_data_factory():
    from randovania.games.blank.exporter.patch_data_factory import BlankPatchDataFactory
    return BlankPatchDataFactory


def _exporter():
    from randovania.games.blank.exporter.game_exporter import BlankGameExporter
    return BlankGameExporter()


game_data: game.GameData = game.GameData(
    short_name="Blank",
    long_name="Blank Development Game",
    development_state=game.DevelopmentState.DEVELOPMENT,

    presets=[
        {
            "path": "starter_preset.rdvpreset"
        },
    ],

    faq=[],

    layout=game.GameLayout(
        configuration=layout.BlankConfiguration,
        cosmetic_patches=layout.BlankCosmeticPatches,
        preset_describer=GamePresetDescriber(),
    ),

    options=_options,

    gui=_gui,

    generator=_generator,

    patch_data_factory=_patch_data_factory,

    exporter=_exporter,
)
