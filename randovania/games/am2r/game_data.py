from __future__ import annotations

from randovania.games import game
from randovania.games.am2r import layout
from randovania.layout.preset_describer import GamePresetDescriber


def _options():
    from randovania.games.am2r.exporter.options import AM2RPerGameOptions
    return AM2RPerGameOptions


def _gui() -> game.GameGui:
    from randovania.games.am2r import gui

    return game.GameGui(
        game_tab=gui.AM2RGameTabWidget,
        tab_provider=gui.preset_tabs,
        cosmetic_dialog=gui.AM2RCosmeticPatchesDialog,
        export_dialog=gui.AM2RGameExportDialog,
        progressive_item_gui_tuples=(),
        spoiler_visualizer=(),
    )


def _generator() -> game.GameGenerator:
    from randovania.games.am2r import generator
    from randovania.generator.hint_distributor import AllJokesHintDistributor

    return game.GameGenerator(
        pickup_pool_creator=generator.pool_creator,
        bootstrap=generator.AM2RBootstrap(),
        base_patches_factory=generator.AM2RBasePatchesFactory(),
        hint_distributor=AllJokesHintDistributor(),
    )


def _patch_data_factory():
    from randovania.games.am2r.exporter.patch_data_factory import AM2RPatchDataFactory
    return AM2RPatchDataFactory


def _exporter():
    from randovania.games.am2r.exporter.game_exporter import AM2RGameExporter
    return AM2RGameExporter()

game_data: game.GameData = game.GameData(
    short_name="AM2R",
    long_name="Another Metroid 2 Remake",
    development_state=game.DevelopmentState.EXPERIMENTAL,

    presets=[
        {
            "path": "starter_preset.rdvpreset"
        },
    ],

    faq=[
        ("Which versions of AM2R are supported?",
         "Only version 1.5.5 is supported. "
         "Currently there are no plans to support other versions."),
        ("Why can I not fire Missiles / Super Missiles / Power Bombs?",
         "You likely have the 'Required Mains' option enabled. This means you first "
         "need to find the Launcher for your Missiles / Super Missiles / Power Bombs before you can use them."),
        ("I saved in a place that I can't get out of, what do I do?",
         "You can use the 'Restart from Start Location' option, which will "
         "reload your last save but make you spawn at the original start location."),
        ("When does Serris spawn?",
         "Serris spawns once you collect the vanilla Ice Beam location in Distribution Center."),
        ("Can I defeat Serris without Ice Beam?",
         "Yes, Serris automatically changes her weakness to not "
         "require Ice Beam if you fight her before acquiring it."),
        ("Where can I find the Wisdom Septoggs?", "There are seven Wisdom Septoggs. They can can be found in:\n\n"
            "- Main Caves - Research Site Storage\n"
            "- Golden Temple - Breeding Grounds Hub\n"
            "- Hydro Station - Breeding Grounds Lobby\n"
            "- Industrial Complex - Breeding Grounds Fly Stadium\n"
            "- The Tower - Tower Exterior North\n"
            "- Distribution Center - Distribution Facility Tower East\n"
            "- The Nest - Depths Shinespark Cave East"),
        ("What are shinies?",
         "Some items have a 1 in 1024 chance of being a Pokémon-style shiny: "
         "they look different but behave entirely the same as normal. "
         "In a multiworld game, only your own items can be shiny.")

    ],

    layout=game.GameLayout(
        configuration=layout.AM2RConfiguration,
        cosmetic_patches=layout.AM2RCosmeticPatches,
        preset_describer=GamePresetDescriber(),
    ),

    options=_options,

    gui=_gui,

    generator=_generator,

    patch_data_factory=_patch_data_factory,

    exporter=_exporter,

    multiple_start_nodes_per_area=False,
)
