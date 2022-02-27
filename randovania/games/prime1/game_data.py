from randovania.games import game
from randovania.games.prime1.layout.preset_describer import (
    PrimePresetDescriber,
)
from randovania.games.prime1.layout.prime_configuration import PrimeConfiguration
from randovania.games.prime1.layout.prime_cosmetic_patches import PrimeCosmeticPatches


def _options():
    from randovania.games.prime1.exporter.options import PrimePerGameOptions
    return PrimePerGameOptions


def _gui() -> game.GameGui:
    from randovania.gui.game_details.teleporter_details_tab import TeleporterDetailsTab
    from randovania.games.prime1 import gui

    return game.GameGui(
        tab_provider=gui.prime1_preset_tabs,
        cosmetic_dialog=gui.PrimeCosmeticPatchesDialog,
        export_dialog=gui.PrimeGameExportDialog,
        spoiler_visualizer=(TeleporterDetailsTab,),
        help_widget=lambda: gui.PrimeHelpWidget(),
    )


def _generator() -> game.GameGenerator:
    from randovania.games.prime1.generator.item_pool.pool_creator import prime1_specific_pool
    from randovania.games.prime1.generator.bootstrap import PrimeBootstrap
    from randovania.generator.base_patches_factory import PrimeTrilogyBasePatchesFactory
    from randovania.generator.hint_distributor import AllJokesHintDistributor

    return game.GameGenerator(
        item_pool_creator=prime1_specific_pool,
        bootstrap=PrimeBootstrap(),
        base_patches_factory=PrimeTrilogyBasePatchesFactory(),
        hint_distributor=AllJokesHintDistributor(),
    )


def _patch_data_factory():
    from randovania.games.prime1.exporter.patch_data_factory import PrimePatchDataFactory
    return PrimePatchDataFactory


def _exporter():
    from randovania.games.prime1.exporter.game_exporter import PrimeGameExporter
    return PrimeGameExporter()


game_data: game.GameData = game.GameData(
    short_name="Prime",
    long_name="Metroid Prime",
    development_state=game.DevelopmentState.STABLE,

    presets=[
        {
            "path": "starter_preset.rdvpreset"
        },
        {
            "path": "moderate_challenge.rdvpreset"
        },
    ],

    faq=[
        ("An item collection message sometimes shows up when collecting items, even when disabled. Why?",

         "In a multiworld, you must not collect items for other players too quickly. "
         "To avoid issues, the message box is forced in situations a problem could happen. "
         "For more details on the problem, check *Randovania Help -> Multiworld*."),

        ("What is a Shiny Missile Expansion?",

         "Missile Expansions have a 1 in 1024 of being Pokémon-style shiny: "
         "they look different but behave entirely the same as normal.\n"
         "In a multiworld game, only your own Missile Expansions can be shiny."),

        ("What versions of the game are supported?",

         "All Gamecube versions are supported. If it plays with tank controls, it can be randomized. "
         "Wii/Trilogy version is not supported at this time."),

        ("Won't seeds requiring glitches be incompletable on PAL, JP, and Player's Choice "
         "due to the version differences from NTSC 0-00?",

         "When the output ISO is generated, the input version is automatically detected, and any bug or sequence break "
         "fixes present on that version are undone. This reverts the game to be functionally equivalent to NTSC 0-00, "
         "meaning that all versions of Prime are guaranteed to be logically completable when randomized."),
    ],

    layout=game.GameLayout(
        configuration=PrimeConfiguration,
        cosmetic_patches=PrimeCosmeticPatches,
        preset_describer=PrimePresetDescriber()
    ),

    options=_options,

    gui=_gui,

    generator=_generator,

    patch_data_factory=_patch_data_factory,

    exporter=_exporter,
)
