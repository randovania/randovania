from __future__ import annotations

from randovania.games import game
from randovania.games.prime2.layout.echoes_configuration import EchoesConfiguration
from randovania.games.prime2.layout.echoes_cosmetic_patches import EchoesCosmeticPatches
from randovania.games.prime2.layout.preset_describer import EchoesPresetDescriber


def _options():
    from randovania.games.prime2.exporter.options import EchoesPerGameOptions

    return EchoesPerGameOptions


def _gui() -> game.GameGui:
    from randovania.games.common.prime_family.gui.prime_trilogy_teleporter_details_tab import (
        PrimeTrilogyTeleporterDetailsTab,
    )
    from randovania.games.prime2 import gui
    from randovania.games.prime2.pickup_database import progressive_items

    return game.GameGui(
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


def _generator() -> game.GameGenerator:
    from randovania.games.prime2.generator.base_patches_factory import EchoesBasePatchesFactory
    from randovania.games.prime2.generator.bootstrap import EchoesBootstrap
    from randovania.games.prime2.generator.hint_distributor import EchoesHintDistributor
    from randovania.games.prime2.generator.pickup_pool.pool_creator import echoes_specific_pool

    return game.GameGenerator(
        pickup_pool_creator=echoes_specific_pool,
        bootstrap=EchoesBootstrap(),
        base_patches_factory=EchoesBasePatchesFactory(),
        hint_distributor=EchoesHintDistributor(),
    )


def _patch_data_factory():
    from randovania.games.prime2.exporter.patch_data_factory import EchoesPatchDataFactory

    return EchoesPatchDataFactory


def _exporter():
    from randovania.games.prime2.exporter.game_exporter import EchoesGameExporter

    return EchoesGameExporter()


# ruff: noqa: E501

game_data: game.GameData = game.GameData(
    short_name="Echoes",
    long_name="Metroid Prime 2: Echoes",
    development_state=game.DevelopmentState.STABLE,
    presets=[
        {"path": "starter_preset.rdvpreset"},
        {"path": "darkszero_deluxe.rdvpreset"},
        {"path": "fewest_changes.rdvpreset"},
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
    ],
    web_info=game.GameWebInfo(
        what_can_randomize=[
            "All items including Temple Keys",
            "Elevator destinations",
            "Starting locations",
            "Door locks",
            "Translator gate requirements",
        ],
        need_to_play=[
            "An ISO of any NTSC-U or PAL Gamecube release of the game",
            "A modded Wii, or Dolphin Emulator",
        ],
    ),
    layout=game.GameLayout(
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
