from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games import game
from randovania.games.samus_returns import layout
from randovania.games.samus_returns.layout.preset_describer import MSRPresetDescriber
from randovania.games.samus_returns.pickup_database import progressive_items

if TYPE_CHECKING:
    from randovania.exporter.game_exporter import GameExporter
    from randovania.exporter.patch_data_factory import PatchDataFactory
    from randovania.interface_common.options import PerGameOptions


def _options() -> type[PerGameOptions]:
    from randovania.games.samus_returns.exporter.options import MSRPerGameOptions

    return MSRPerGameOptions


def _gui() -> game.GameGui:
    from randovania.games.samus_returns import gui

    return game.GameGui(
        game_tab=gui.MSRGameTabWidget,
        tab_provider=gui.msr_preset_tabs,
        cosmetic_dialog=gui.MSRCosmeticPatchesDialog,
        export_dialog=gui.MSRGameExportDialog,
        progressive_item_gui_tuples=progressive_items.tuples(),
        spoiler_visualizer=(gui.MSRHintDetailsTab, gui.MSRTeleporterDetailsTab),
    )


def _patch_data_factory() -> type[PatchDataFactory]:
    from randovania.games.samus_returns.exporter.patch_data_factory import MSRPatchDataFactory

    return MSRPatchDataFactory


def _exporter() -> GameExporter:
    from randovania.games.samus_returns.exporter.game_exporter import MSRGameExporter

    return MSRGameExporter()


def _generator() -> game.GameGenerator:
    from randovania.games.samus_returns import generator
    from randovania.games.samus_returns.generator.bootstrap import MSRBootstrap
    from randovania.games.samus_returns.generator.hint_distributor import MSRHintDistributor

    return game.GameGenerator(
        pickup_pool_creator=generator.pool_creator,
        bootstrap=MSRBootstrap(),
        base_patches_factory=generator.MSRBasePatchesFactory(),
        hint_distributor=MSRHintDistributor(),
    )


def _hash_words() -> list[str]:
    from randovania.games.samus_returns.hash_words import HASH_WORDS

    return HASH_WORDS


game_data: game.GameData = game.GameData(
    short_name="MSR",
    long_name="Metroid: Samus Returns",
    development_state=game.DevelopmentState.STABLE,
    presets=[
        {"path": "starter_preset.rdvpreset"},
        {"path": "multiworld-starter-preset.rdvpreset"},
    ],
    faq=[
        (
            "What are the icons on the bottom of the HUD?",
            "From left to right the HUD shows: the amount of DNA you currently have, the amount of DNA "
            "collected per area out of how many in that area, "
            "and the amount of Metroids that are still alive. ",
        ),
        (
            "Do I still need to beat Metroids and collect DNA to progress areas?",
            "No, you do not. All the hazardous liquid has already been drained. "
            "Metroids can now drop any item in the game, as well as DNA.",
        ),
        (
            "Do I have to beat the Queen Metroid to beat the game?",
            "No. In order to beat the game, you must collect the required Metroid DNA, "
            "find the Baby, and defeat Proteus Ridley.",
        ),
        (
            "How much Metroid DNA is required to beat the game?",
            "The amount of required DNA is configurable from 0 to 39 DNA. ",
        ),
        (
            "How do I access Proteus Ridley?",
            "After having collected the Baby and all DNA, enter the transition between the Surface Teleporter and "
            "Landing Site. Going through the transition without the requirements will give you "
            "access to the Ship instead.",
        ),
        (
            "Are there any hints?",
            "All Chozo Seals have been repurposed to provide a hint to "
            "an item somewhere in the world. The region the item is located "
            "will be specified."
            "\n\n"
            "New seals have been added in all areas, which hint at the location "
            "of DNA. Additionally, the HUD also shows how much DNA is located in each area. "
            "See the `Hints` tab for more information.",
        ),
        (
            "Why is this pickup not animating?",
            "While progressive pickups update to have the correct model, "
            "due to limitations these models are not animated.",
        ),
        (
            "I collected Beam Burst, but I cannot use it.",
            "Beam Burst requires at least the Wave Beam to function.",
        ),
        (
            "What are Reserve Tanks?",
            "Reserve Tanks are items that restore a certain ammo type when depleted. "
            "In vanilla, these tanks can be unlocked by using certain amiibo, "
            "but in the randomizer, this has been changed to make them be actual pickups."
            "\n\n"
            "By default, the Energy Reserve Tank restores 299 Energy, the Aeion Reserve Tank "
            "restores 500 Aeion, and the Missile Reserve Tank restores 30 Missiles or "
            "10 Super Missiles. Note that when the Missile Reserve Tank is depeleted, "
            "it only restores whatever ammo was last used, and not both.",
        ),
        (
            "I collected the Missile Reserve Tank, but I cannot see nor use it.",
            "Due to limitations, the Missile Reserve Tank will remain deactivated "
            "until the Missile Launcher is in your inventory. This prevents a bug where "
            "the reserve will activate even if you have no usable Missiles.",
        ),
        (
            "Why did my Power Bombs disappear during the Diggernaut fight?",
            "Due to technical limitations, Power Bombs are temporarily disabled while fighting Diggernaut. "
            "If Diggernaut is defeated or a checkpoint/save is reloaded, your Power Bombs will be re-enabled.",
        ),
    ],
    web_info=game.GameWebInfo(
        what_can_randomize=[
            "All items, including ones normally locked behind amiibo",
            "Starting locations",
            "Door locks",
            "Elevator destinations",
            "A new goal has been added (DNA Hunt)",
        ],
        need_to_play=[
            "A modded 3DS with Luma3DS, or Citra",
            "A dumped RomFS of your original game. Any region works.",
        ],
    ),
    hash_words=_hash_words(),
    layout=game.GameLayout(
        configuration=layout.MSRConfiguration,
        cosmetic_patches=layout.MSRCosmeticPatches,
        preset_describer=MSRPresetDescriber(),
    ),
    options=_options,
    gui=_gui,
    generator=_generator,
    patch_data_factory=_patch_data_factory,
    exporter=_exporter,
    defaults_available_in_game_sessions=True,
    multiple_start_nodes_per_area=True,
)
