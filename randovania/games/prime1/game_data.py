from randovania.games.game import GameData, GameGenerator, GameGui, GameLayout, GamePresetDescriber
from randovania.games.prime1.generator.bootstrap import PrimeBootstrap
from randovania.games.prime1.generator.item_pool.pool_creator import prime1_specific_pool
from randovania.games.prime1.layout.preset_describer import prime_expected_items, prime_unexpected_items, \
    prime_format_params
from randovania.games.prime1.layout.prime_configuration import PrimeConfiguration
from randovania.games.prime1.layout.prime_cosmetic_patches import PrimeCosmeticPatches
from randovania.games.prime1.patcher.randomprime_patcher import RandomprimePatcher
from randovania.generator.base_patches_factory import PrimeTrilogyBasePatchesFactory


def _prime_gui():
    from randovania.games.prime1.gui.preset_settings import prime1_preset_tabs
    from randovania.games.prime1.gui.dialog.prime_cosmetic_patches_dialog import PrimeCosmeticPatchesDialog
    from randovania.gui.game_details.teleporter_details_tab import TeleporterDetailsTab

    return GameGui(
        tab_provider=prime1_preset_tabs,
        cosmetic_dialog=PrimeCosmeticPatchesDialog,
        input_file_text=("an ISO file", "the Nintendo Gamecube", "Gamecube ISO"),
        spoiler_visualizer=(TeleporterDetailsTab,),
    )


game_data: GameData = GameData(
    short_name="Prime",
    long_name="Metroid Prime",
    experimental=False,

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

    layout=GameLayout(
        configuration=PrimeConfiguration,
        cosmetic_patches=PrimeCosmeticPatches,
        preset_describer=GamePresetDescriber(
            expected_items=prime_expected_items,
            unexpected_items=prime_unexpected_items,
            format_params=prime_format_params
        )
    ),

    gui=_prime_gui,

    generator=GameGenerator(
        item_pool_creator=prime1_specific_pool,
        bootstrap=PrimeBootstrap(),
        base_patches_factory=PrimeTrilogyBasePatchesFactory()
    ),

    patcher=RandomprimePatcher()
)
