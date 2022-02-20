from randovania.games import game
from randovania.games.game import GameData, GameLayout, GamePresetDescriber
from randovania.games.prime2.layout.echoes_configuration import EchoesConfiguration
from randovania.games.prime2.layout.echoes_cosmetic_patches import EchoesCosmeticPatches
from randovania.games.prime2.layout.preset_describer import (
    echoes_format_params, echoes_unexpected_items,
    echoes_expected_items
)
from randovania.games.prime2.patcher.claris_patcher import ClarisPatcher


def _gui() -> game.GameGui:
    from randovania.gui.game_details.teleporter_details_tab import TeleporterDetailsTab
    from randovania.games.prime2.item_database import prime2_progressive_items
    from randovania.games.prime2.gui.dialog.echoes_cosmetic_patches_dialog import EchoesCosmeticPatchesDialog
    from randovania.games.prime2.gui.preset_settings import prime2_preset_tabs
    from randovania.games.prime2.gui.translator_gate_details_tab import TranslatorGateDetailsTab
    from randovania.games.prime2.gui.hint_details_tab import EchoesHintDetailsTab
    from randovania.games.prime2.gui.echoes_help_widget import EchoesHelpWidget

    return game.GameGui(
        tab_provider=prime2_preset_tabs,
        cosmetic_dialog=EchoesCosmeticPatchesDialog,
        input_file_text=("an ISO file", "the Nintendo Gamecube", "Gamecube ISO"),
        progressive_item_gui_tuples=prime2_progressive_items.gui_tuples(),
        spoiler_visualizer=(TeleporterDetailsTab, TranslatorGateDetailsTab, EchoesHintDetailsTab),
        help_widget=lambda: EchoesHelpWidget(),
    )


def _generator() -> game.GameGenerator:
    from randovania.games.prime2.generator.base_patches_factory import EchoesBasePatchesFactory
    from randovania.games.prime2.generator.bootstrap import EchoesBootstrap
    from randovania.games.prime2.generator.item_pool.pool_creator import echoes_specific_pool
    from randovania.games.prime2.generator.hint_distributor import EchoesHintDistributor

    return game.GameGenerator(
        item_pool_creator=echoes_specific_pool,
        bootstrap=EchoesBootstrap(),
        base_patches_factory=EchoesBasePatchesFactory(),
        hint_distributor=EchoesHintDistributor(),
    )


game_data: GameData = GameData(
    short_name="Echoes",
    long_name="Metroid Prime 2: Echoes",
    experimental=False,

    presets=[
        {
            "path": "starter_preset.rdvpreset"
        },
        {
            "path": "darkszero_deluxe.rdvpreset"
        },
        {
            "path": "fewest_changes.rdvpreset"
        }
    ],

    faq=[
        ("I can't use this spider track, even though I have Spider Ball!",

         """The following rooms have surprising vanilla behaviour about their spider tracks:

#### Main Reactor (Agon Wastes)

The spider tracks only works after you beat Dark Samus 1 and reload the room. When playing with no tricks, this means you need Dark Beam to escape the room.

#### Dynamo Works (Sanctuary Fortress)

The spider tracks only works after you beat Spider Guardian. When playing with no tricks, you can't leave this way until you do that.

#### Spider Guardian fight (Sanctuary Fortress)

During the fight, the spider tracks only works in the first and last phases. After the fight, they all work normally.
This means you need Boost Ball to fight Spider Guardian."""),

        ("Where is the Flying Ing Cache inside Dark Oasis?",

         "The Flying Ing Cache in this room appears only after you collect the item that appears after defeating Power Bomb Guardian."),

        ("When causes the Dark Missile Trooper to spawn?",

         "Defeating the Bomb Guardian."),

        ("What causes the Missile Expansion on top of the GFMC Compound to spawn?",

         "Collecting the item that appears after defeating the Jump Guardian."),

        ("Why isn't the elevator in Torvus Temple working?",

         "In order to open the elevator, you also need to pick the item in Torvus Energy Controller."),

        ("Why can't I see the echo locks in Mining Plaza even when using the Echo Visor?",

         "You need to beat Amorbis and then return the Agon Energy in order for these echo locks to appear."),

        ("Why can't I cross the door between Underground Transport and Torvus Temple?",

         "The energy gate that disappears after the pirate fight in Torvus Temple blocks this door."),
    ],

    layout=GameLayout(
        configuration=EchoesConfiguration,
        cosmetic_patches=EchoesCosmeticPatches,
        preset_describer=GamePresetDescriber(
            expected_items=echoes_expected_items,
            unexpected_items=echoes_unexpected_items,
            format_params=echoes_format_params,
        )
    ),

    gui=_gui,

    generator=_generator,

    patcher=ClarisPatcher()
)
