from __future__ import annotations

import randovania.game.data
import randovania.game.development_state
import randovania.game.generator
import randovania.game.gui
import randovania.game.layout
import randovania.game.web_info
from randovania.games.prime2.layout.echoes_configuration import EchoesConfiguration
from randovania.games.prime2.layout.echoes_cosmetic_patches import EchoesCosmeticPatches
from randovania.games.prime2.layout.preset_describer import EchoesPresetDescriber


def _options():
    from randovania.games.prime2.exporter.options import EchoesPerGameOptions

    return EchoesPerGameOptions


def _gui() -> randovania.game.gui.GameGui:
    from randovania.games.common.prime_family.gui.prime_trilogy_teleporter_details_tab import (
        PrimeTrilogyTeleporterDetailsTab,
    )
    from randovania.games.prime2 import gui
    from randovania.games.prime2.layout import progressive_items

    return randovania.game.gui.GameGui(
        tab_provider=gui.prime2_preset_tabs,
        cosmetic_dialog=gui.EchoesCosmeticPatchesDialog,
        export_dialog=gui.EchoesGameExportDialog,
        progressive_item_gui_tuples=progressive_items.tuples(),
        spoiler_visualizer=(
            PrimeTrilogyTeleporterDetailsTab,
            gui.TranslatorGateDetailsTab,
            gui.PortalDetailsTab,
            gui.EchoesHintDetailsTab,
        ),
        game_tab=gui.EchoesGameTabWidget,
    )


def _generator() -> randovania.game.generator.GameGenerator:
    from randovania.games.prime2.generator.base_patches_factory import EchoesBasePatchesFactory
    from randovania.games.prime2.generator.bootstrap import EchoesBootstrap
    from randovania.games.prime2.generator.hint_distributor import EchoesHintDistributor
    from randovania.games.prime2.generator.pickup_pool.pool_creator import echoes_specific_pool
    from randovania.generator.filler.weights import ActionWeights

    return randovania.game.generator.GameGenerator(
        pickup_pool_creator=echoes_specific_pool,
        bootstrap=EchoesBootstrap(),
        base_patches_factory=EchoesBasePatchesFactory(),
        hint_distributor=EchoesHintDistributor(),
        action_weights=ActionWeights(),
    )


def _patch_data_factory():
    from randovania.games.prime2.exporter.patch_data_factory import EchoesPatchDataFactory

    return EchoesPatchDataFactory


def _exporter():
    from randovania.games.prime2.exporter.game_exporter import EchoesGameExporter

    return EchoesGameExporter()


def _hash_words() -> list[str]:
    from randovania.games.prime2.hash_words import HASH_WORDS

    return HASH_WORDS


# ruff: noqa: E501

game_data: randovania.game.data.GameData = randovania.game.data.GameData(
    short_name="Echoes",
    long_name="Metroid Prime 2: Echoes",
    development_state=randovania.game.development_state.DevelopmentState.STABLE,
    presets=[
        {"path": "starter_preset.rdvpreset"},
        {"path": "darkszero_deluxe.rdvpreset"},
    ],
    faq=[
        (
            "I can't use this spider track, even though I have Spider Ball!",
            """The following rooms have surprising vanilla behaviour about their spider tracks:

#### Main Reactor (Agon Wastes)

The spider tracks only works after you beat Dark Samus 1 and reload the room. When playing with no tricks, this means you need Dark Beam to escape the room.

#### Dynamo Works (Sanctuary Fortress)

The spider tracks only works after you beat Spider Guardian. When playing with no tricks, you can't leave this way until you do that.

#### Spider Guardian fight (Sanctuary Fortress)

During the fight, the spider tracks only works in the first and last phases. After the fight, they all work normally.
This means you need Boost Ball to fight Spider Guardian.""",
        ),
        (
            "Where is the Flying Ing Cache inside Dark Oasis?",
            "The Flying Ing Cache in this room appears only after you collect the item that appears after defeating Power Bomb Guardian.",
        ),
        ("What causes the Dark Missile Trooper to spawn?", "Defeating the Bomb Guardian."),
        (
            "What causes the Missile Expansion on top of the GFMC Compound to spawn?",
            "Collecting the item that appears after defeating the Jump Guardian.",
        ),
        (
            "Why isn't the elevator in Torvus Temple working?",
            "In order to open the elevator, you also need to pick the item in Torvus Energy Controller.",
        ),
        (
            "Why can't I see the echo locks in Mining Plaza even when using the Echo Visor?",
            "You need to beat Amorbis and then return the Agon Energy in order for these echo locks to appear.",
        ),
        (
            "Why can't I cross the door between Underground Transport and Torvus Temple?",
            "The energy gate that disappears after the pirate fight in Torvus Temple blocks this door.",
        ),
        (
            "Why can't I use the Kinetic Orb Cannon in Sanctuary Entrance?",
            "The morph cannon will only be active once the scan post has been scanned and the room has been reloaded.",
        ),
        (
            "How do I use the light beam transports?",
            """To use a light beam transport, simply enter the light beams/holograms with Light Suit. The following rooms behave differently and do not require Light Suit, and may have additional requirements in order to use the transports:

#### Energy Controllers
The light beam transports that are unlocked upon returning the Sanctuary Energy and going back to Main Energy Controller.

#### Sky Temple Gateway (Sky Temple Grounds)

The light beam transport unlocked when returning all the Sky Temple Keys.

#### Sky Temple Energy Controller (Sky Temple)

Taking the transport hologram at the center of this room.""",
        ),
    ],
    web_info=randovania.game.web_info.GameWebInfo(
        what_can_randomize=[
            "All items including Temple Keys",
            "Elevator destinations",
            "Starting locations",
            "Door locks",
            "Translator gate requirements",
        ],
        need_to_play=[
            "An ISO of any NTSC-U or PAL GameCube release of the game",
            "A modded Wii, or Dolphin Emulator",
        ],
    ),
    hash_words=_hash_words(),
    layout=randovania.game.layout.GameLayout(
        configuration=EchoesConfiguration,
        cosmetic_patches=EchoesCosmeticPatches,
        preset_describer=EchoesPresetDescriber(),
    ),
    options=_options,
    gui=_gui,
    generator=_generator,
    patch_data_factory=_patch_data_factory,
    exporter=_exporter,
    defaults_available_in_game_sessions=True,
)
