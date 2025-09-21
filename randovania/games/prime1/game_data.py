from __future__ import annotations

from typing import TYPE_CHECKING

import randovania.game.data
import randovania.game.development_state
import randovania.game.generator
import randovania.game.gui
import randovania.game.hints
import randovania.game.layout
import randovania.game.web_info
from randovania.games.prime1.db_integrity import find_prime_db_errors
from randovania.games.prime1.layout.preset_describer import (
    PrimePresetDescriber,
)
from randovania.games.prime1.layout.prime_configuration import PrimeConfiguration
from randovania.games.prime1.layout.prime_cosmetic_patches import PrimeCosmeticPatches

if TYPE_CHECKING:
    from randovania.exporter.game_exporter import GameExporter
    from randovania.exporter.patch_data_factory import PatchDataFactory
    from randovania.interface_common.options import PerGameOptions


def _options() -> type[PerGameOptions]:
    from randovania.games.prime1.exporter.options import PrimePerGameOptions

    return PrimePerGameOptions


def _gui() -> randovania.game.gui.GameGui:
    from randovania.games.common.prime_family.gui.prime_trilogy_teleporter_details_tab import (
        PrimeTrilogyTeleporterDetailsTab,
    )
    from randovania.games.prime1 import gui

    return randovania.game.gui.GameGui(
        tab_provider=gui.prime1_preset_tabs,
        cosmetic_dialog=gui.PrimeCosmeticPatchesDialog,
        export_dialog=gui.PrimeGameExportDialog,
        spoiler_visualizer=(PrimeTrilogyTeleporterDetailsTab,),
        game_tab=gui.PrimeGameTabWidget,
    )


def _generator() -> randovania.game.generator.GameGenerator:
    from randovania.games.prime1.generator.base_patches_factory import (
        PrimeBasePatchesFactory,
    )
    from randovania.games.prime1.generator.bootstrap import PrimeBootstrap
    from randovania.games.prime1.generator.pickup_pool.pool_creator import (
        prime1_specific_pool,
    )
    from randovania.generator.filler.weights import ActionWeights

    return randovania.game.generator.GameGenerator(
        pickup_pool_creator=prime1_specific_pool,
        bootstrap=PrimeBootstrap(),
        base_patches_factory=PrimeBasePatchesFactory(),
        action_weights=ActionWeights(),
    )


def _hints() -> randovania.game.hints.GameHints:
    from randovania.games.prime1.hint_distributor import PrimeHintDistributor

    return randovania.game.hints.GameHints(
        hint_distributor=PrimeHintDistributor(),
        specific_pickup_hints={
            "artifacts": randovania.game.hints.SpecificHintDetails(
                long_name="Chozo Artifacts",
                description="This controls how precise the hints for Chozo Artifacts in Artifact Temple are.",
            ),
            "phazon_suit": randovania.game.hints.SpecificHintDetails(
                long_name="Phazon Suit",
                description="This controls how precise the hint for Phazon Suit in Impact Crater is.",
                disabled_details="No hint is added.",
                hide_area_details=(
                    "A scan post will be placed in Crater Entry Point "
                    "revealing Phazon Suit's region (e.g. Player 2's Phazon Mines)."
                ),
                precise_details="Same as above, but shows the exact area name as well.",
            ),
        },
    )


def _patch_data_factory() -> type[PatchDataFactory]:
    from randovania.games.prime1.exporter.patch_data_factory import (
        PrimePatchDataFactory,
    )

    return PrimePatchDataFactory


def _exporter() -> GameExporter:
    from randovania.games.prime1.exporter.game_exporter import PrimeGameExporter

    return PrimeGameExporter()


def _hash_words() -> list[str]:
    from randovania.games.prime1.hash_words import HASH_WORDS

    return HASH_WORDS


game_data: randovania.game.data.GameData = randovania.game.data.GameData(
    short_name="Prime",
    long_name="Metroid Prime",
    development_state=randovania.game.development_state.DevelopmentState.STABLE,
    presets=[
        "starter_preset.rdvpreset",
        "moderate_challenge.rdvpreset",
        "april_fools_2022.rdvpreset",
    ],
    faq=[
        (
            "An item collection message sometimes shows up when collecting items, even when disabled. Why?",
            "In a multiworld, you must not collect items for other players too quickly. "
            "To avoid issues, the message box is forced in situations a problem could happen. "
            "For more details on the problem, check *Randovania Help -> Multiworld*.",
        ),
        (
            "What is a Shiny Missile Expansion?",
            "Missile Expansions have a 1 in 1024 of being Pokémon-style shiny: "
            "they look different but behave entirely the same as normal.\n\n"
            "In a multiworld game, only your own Missile Expansions can be shiny.",
        ),
        (
            "What versions of the game are supported?",
            "All Gamecube versions are supported. If it plays with tank controls, it can be randomized. "
            "Wii/Trilogy version is not supported at this time.",
        ),
        (
            "Won't seeds requiring glitches be incompletable on PAL, JP, and Player's Choice "
            "due to the version differences from NTSC 0-00?",
            "When the output ISO is generated, the input version is automatically detected, and any bug or sequence "
            "break fixes present on that version are undone. This reverts the game to be functionally equivalent to "
            "NTSC 0-00, meaning that all versions of Prime are guaranteed to be logically completable when randomized.",
        ),
        (
            "Why do I not take heat damage in some rooms in Magmoor, despite not having Varia Suit?",
            "Some rooms in Magmoor are not coded to be superheated. These include:\n"
            "- All Elevator Rooms\n"
            "- Burning Trail\n"
            "- Storage Cavern\n"
            "- Every room after Twin Fires Tunnel\n",
        ),
    ],
    web_info=randovania.game.web_info.GameWebInfo(
        what_can_randomize=[
            "All items including Artifacts",
            "Elevator destinations",
            "Starting locations",
            "Door locks",
        ],
        need_to_play=[
            "An ISO of any GameCube release of the game",
            "A modded Wii, or Dolphin Emulator",
        ],
    ),
    hash_words=_hash_words(),
    layout=randovania.game.layout.GameLayout(
        configuration=PrimeConfiguration,
        cosmetic_patches=PrimeCosmeticPatches,
        preset_describer=PrimePresetDescriber(),
    ),
    options=_options,
    gui=_gui,
    generator=_generator,
    hints=_hints,
    patch_data_factory=_patch_data_factory,
    exporter=_exporter,
    defaults_available_in_game_sessions=True,
    logic_db_integrity=find_prime_db_errors,
)
