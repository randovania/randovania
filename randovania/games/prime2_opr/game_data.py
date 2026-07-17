from __future__ import annotations

import typing

import randovania
import randovania.game.data
import randovania.game.development_state
import randovania.game.game_test_data
import randovania.game.generator
import randovania.game.gui
import randovania.game.hints
import randovania.game.layout
import randovania.game.web_info
from randovania.games.prime2_opr import layout

if typing.TYPE_CHECKING:
    from randovania.exporter.game_exporter import GameExporter
    from randovania.exporter.patch_data_factory import PatchDataFactory
    from randovania.interface_common.options import PerGameOptions


def _options() -> type[PerGameOptions]:
    from randovania.games.prime2_opr.exporter.options import EchoesOPRPerGameOptions

    return EchoesOPRPerGameOptions


def _gui() -> randovania.game.gui.GameGui:
    from randovania.games.common.prime_family.gui.prime_trilogy_teleporter_details_tab import (
        PrimeTrilogyTeleporterDetailsTab,
    )
    from randovania.games.prime2.gui import PortalDetailsTab, TranslatorGateDetailsTab
    from randovania.games.prime2_opr import gui
    from randovania.games.prime2_opr.layout import progressive_items
    from randovania.gui.game_details.hint_details_tab import HintDetailsTab

    return randovania.game.gui.GameGui(
        game_tab=gui.EchoesOPRGameTabWidget,
        tab_provider=gui.preset_tabs,
        cosmetic_dialog=gui.EchoesOPRCosmeticPatchesDialog,
        export_dialog=gui.EchoesOPRGameExportDialog,
        progressive_item_gui_tuples=progressive_items.tuples(),
        spoiler_visualizer=(
            PrimeTrilogyTeleporterDetailsTab,
            TranslatorGateDetailsTab,
            PortalDetailsTab,
            HintDetailsTab,
        ),
    )


def _generator() -> randovania.game.generator.GameGenerator:
    from randovania.games.prime2.generator.pickup_pool.pool_creator import echoes_specific_pool
    from randovania.games.prime2_opr import generator
    from randovania.generator.filler.weights import ActionWeights

    return randovania.game.generator.GameGenerator(
        pickup_pool_creator=echoes_specific_pool,
        bootstrap=generator.EchoesOPRBootstrap(),
        base_patches_factory=generator.EchoesOPRBasePatchesFactory(),
        action_weights=ActionWeights(),
    )


def _hints() -> randovania.game.hints.GameHints:
    from randovania.games.prime2_opr import generator

    return randovania.game.hints.GameHints(
        hint_distributor=generator.EchoesOPRHintDistributor(),
        specific_pickup_hints={
            "sky_temple_keys": randovania.game.hints.SpecificHintDetails(
                long_name="Sky Temple Key Hints",
                description="This controls how precise the hints for Sky Temple Keys in Sky Temple Gateway are.",
            ),
            "dark_temple_keys": randovania.game.hints.SpecificHintDetails(
                long_name="Dark Temple Key Hints",
                description=(
                    "This controls how precise the hints for Dark Temple Keys at their respective gateways are."
                ),
            ),
        },
    )


def _patch_data_factory() -> type[PatchDataFactory]:
    from randovania.games.prime2_opr.exporter.patch_data_factory import EchoesOPRPatchDataFactory

    return EchoesOPRPatchDataFactory


def _exporter() -> GameExporter:
    from randovania.games.prime2_opr.exporter.game_exporter import EchoesOPRGameExporter

    return EchoesOPRGameExporter()


def _hash_words() -> list[str]:
    from randovania.games.prime2.hash_words import HASH_WORDS

    return HASH_WORDS


def _test_data() -> randovania.game.game_test_data.GameTestData:
    return randovania.game.game_test_data.GameTestData(
        expected_seed_hash="QGOUYTAB",
        database_collectable_ignore_events=("Event91", "Event92", "Event97"),
    )


game_data: randovania.game.data.GameData = randovania.game.data.GameData(
    short_name="EchoesOPR",
    long_name="Metroid Prime 2: Echoes (Open Prime Rando)",
    development_state=randovania.game.development_state.DevelopmentState.SOURCE_ONLY,
    presets=["starter_preset.rdvpreset"],
    faq=[
        (
            "Why can't I see the echo locks in Mining Plaza even when using the Echo Visor?",
            "You need to beat Amorbis and then return the Agon Energy in order for these echo locks to appear.",
        ),
        (
            "How do I use the light energy transports?",
            """
To use a light energy transport, simply enter the light energy/holograms with Light Suit.
The following rooms behave differently and do not require Light Suit,
and may have additional requirements in order to use the transports:

#### Energy Controllers
The light energy transports that are unlocked upon returning
the Sanctuary Energy and going back to Main Energy Controller.

#### Sky Temple Gateway (Sky Temple Grounds)

The light energy transport unlocked when returning all the Sky Temple Keys.

#### Sky Temple Energy Controller (Sky Temple)

Taking the transport hologram at the center of this room.
            """,
        ),
    ],
    web_info=randovania.game.web_info.GameWebInfo(
        what_can_randomize=(
            "All items including Temple Keys",
            "Elevator destinations",
            "Portal destinations",
            "Starting locations",
            "Door locks",
            "Translator gate requirements",
        ),
        need_to_play=(
            "An ISO of any NTSC-U or PAL GameCube release of the game",
            "A modded Wii, or Dolphin Emulator",
        ),
    ),
    hash_words=_hash_words(),
    layout=randovania.game.layout.GameLayout(
        configuration=layout.EchoesOPRConfiguration,
        cosmetic_patches=layout.EchoesOPRCosmeticPatches,
        preset_describer=layout.EchoesOPRPresetDescriber(),
    ),
    options=_options,
    gui=_gui,
    generator=_generator,
    hints=_hints,
    patch_data_factory=_patch_data_factory,
    exporter=_exporter,
    test_data=_test_data,
    reject_undocumented_tricks_in_database=False,
)
