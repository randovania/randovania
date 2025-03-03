from __future__ import annotations

from typing import TYPE_CHECKING

import randovania.game.data
import randovania.game.development_state
import randovania.game.generator
import randovania.game.gui
import randovania.game.layout
import randovania.game.web_info
from randovania.games.am2r import layout
from randovania.games.am2r.db_integrity import find_am2r_db_errors

if TYPE_CHECKING:
    from randovania.exporter.game_exporter import GameExporter
    from randovania.exporter.patch_data_factory import PatchDataFactory
    from randovania.interface_common.options import PerGameOptions


def _options() -> type[PerGameOptions]:
    from randovania.games.am2r.exporter.options import AM2RPerGameOptions

    return AM2RPerGameOptions


def _gui() -> randovania.game.gui.GameGui:
    from randovania.games.am2r import gui
    from randovania.games.am2r.layout import progressive_items

    return randovania.game.gui.GameGui(
        game_tab=gui.AM2RGameTabWidget,
        tab_provider=gui.preset_tabs,
        cosmetic_dialog=gui.AM2RCosmeticPatchesDialog,
        export_dialog=gui.AM2RGameExportDialog,
        progressive_item_gui_tuples=progressive_items.tuples(),
        spoiler_visualizer=(gui.AM2RTeleporterDetailsTab,),
    )


def _generator() -> randovania.game.generator.GameGenerator:
    from randovania.games.am2r import generator
    from randovania.games.am2r.generator.hint_distributor import AM2RHintDistributor
    from randovania.generator.filler.weights import ActionWeights

    return randovania.game.generator.GameGenerator(
        pickup_pool_creator=generator.pool_creator,
        bootstrap=generator.AM2RBootstrap(),
        base_patches_factory=generator.AM2RBasePatchesFactory(),
        hint_distributor=AM2RHintDistributor(),
        action_weights=ActionWeights(),
    )


def _patch_data_factory() -> type[PatchDataFactory]:
    from randovania.games.am2r.exporter.patch_data_factory import AM2RPatchDataFactory

    return AM2RPatchDataFactory


def _exporter() -> GameExporter:
    from randovania.games.am2r.exporter.game_exporter import AM2RGameExporter

    return AM2RGameExporter()


def _hash_words() -> list[str]:
    from randovania.games.am2r.hash_words import HASH_WORDS

    return HASH_WORDS


game_data: randovania.game.data.GameData = randovania.game.data.GameData(
    short_name="AM2R",
    long_name="Another Metroid 2 Remake",
    development_state=randovania.game.development_state.DevelopmentState.STABLE,
    presets=[
        {"path": "starter_preset.rdvpreset"},
    ],
    faq=[
        (
            "AM2R already has a built-in randomizer, what does this do differently?",
            "The Randovania implementation provides additional robustness and more features compared to the built-"
            "in randomizer."
            "\n\n"
            "Key features supported by Randovania include, but are not limited to, full item logic, toggleable tricks "
            "and difficulties, Door Lock Rando, and Multiworld support."
            "\n\n"
            "All Metroids now also drop items. This can include progression, expansions, or DNA. DNA are like keys and "
            "are used to enter the path to the Queen. The amount of DNA is configurable and a hint system has been "
            "implemented, which means it's not necessary anymore to fight all the Metroids.",
        ),
        (
            "Which versions of AM2R are supported?",
            "Only version 1.5.5 is supported. Currently there are no plans to support other versions.",
        ),
        (
            "Why can I not fire Missiles / Super Missiles / Power Bombs?",
            "You likely have the 'Required Mains' option enabled. This means you first "
            "need to find the Launcher for your Missiles / Super Missiles / Power Bombs before you can use them.",
        ),
        (
            "Why was the DNA goal chosen, and why does the Starter Preset "
            "require main items / launchers for Missiles / Super Missiles / Power Bombs?",
            "Both were chosen to provide better gameplay and more variety. Killing the same 46 Metroids over "
            "and over again is not only tedious, but also boring. The Metroids dropping items makes Metroid fights "
            "interesting and worthwhile to do as opposed to most players otherwise just ignoring them entirely, while "
            "also not making it mandatory to kill all Metroids.\n"
            "Required mains / launchers causes progression to be more natural, as otherwise it's possible "
            "to break the logic chain and get overpowered by just finding ammo early.",
        ),
        (
            "I saved in a place that I can't get out of, what do I do?",
            "You can use the 'Restart from Start Location' option, which will "
            "reload your last save but make you spawn at the original start location.",
        ),
        (
            "What causes Serris to spawn?",
            "Serris will spawn once you collect the item in Distribution Center - Ice Beam Chamber and then hit "
            "the fight trigger on the left side of the Serris Arena.",
        ),
        (
            "Can I defeat Serris without Ice Beam?",
            "Yes, Serris automatically changes her weakness to not "
            "require Ice Beam if you fight her before acquiring it.",
        ),
        (
            "Where can I find the Hints?",
            "There are eight hints in total, and the map will show "
            "an 'H' icon on places where hints exist. They can can be found in:\n\n"
            "- Main Caves - Research Site Elevator\n"
            "- Golden Temple - Breeding Grounds Hub\n"
            "- Hydro Station - Breeding Grounds Lobby\n"
            "- Industrial Complex - Breeding Grounds Fly Stadium\n"
            "- The Tower - Tower Exterior North\n"
            "- Distribution Center - Distribution Facility Tower East\n"
            "- The Depths - Bubble Lair Shinespark Cave\n"
            "- Genetics Laboratory - Destroyed Chozo Memorial",
        ),
        (
            "What are shinies?",
            "Some items have a 1 in 1024 chance of being a Pokémon-style shiny: "
            "they look different but behave entirely the same as normal. "
            "In a multiworld game, only your own items can be shiny.",
        ),
    ],
    web_info=randovania.game.web_info.GameWebInfo(
        what_can_randomize=[
            "All items",
            "Starting locations",
            "Door locks",
            "Transport Pipe destinations",
            "A new goal has been added (DNA Hunt)",
        ],
        need_to_play=[
            "AM2R version 1.5.5 for either Windows, Linux or macOS",
        ],
    ),
    hash_words=_hash_words(),
    layout=randovania.game.layout.GameLayout(
        configuration=layout.AM2RConfiguration,
        cosmetic_patches=layout.AM2RCosmeticPatches,
        preset_describer=layout.AM2RPresetDescriber(),
    ),
    options=_options,
    gui=_gui,
    generator=_generator,
    patch_data_factory=_patch_data_factory,
    exporter=_exporter,
    multiple_start_nodes_per_area=False,
    defaults_available_in_game_sessions=True,
    logic_db_integrity=find_am2r_db_errors,
)
