from __future__ import annotations

import typing

import randovania.game.data
import randovania.game.development_state
import randovania.game.generator
import randovania.game.gui
import randovania.game.layout
from randovania.games.fusion import layout
from randovania.games.fusion.db_integrity import find_fusion_db_errors
from randovania.games.fusion.layout.preset_describer import FusionPresetDescriber

if typing.TYPE_CHECKING:
    from randovania.exporter.game_exporter import GameExporter
    from randovania.exporter.patch_data_factory import PatchDataFactory
    from randovania.interface_common.options import PerGameOptions


def _options() -> type[PerGameOptions]:
    from randovania.games.fusion.exporter.options import FusionPerGameOptions

    return FusionPerGameOptions


def _gui() -> randovania.game.gui.GameGui:
    from randovania.games.fusion import gui
    from randovania.gui.game_details.hint_details_tab import HintDetailsTab

    return randovania.game.gui.GameGui(
        game_tab=gui.FusionGameTabWidget,
        tab_provider=gui.preset_tabs,
        cosmetic_dialog=gui.FusionCosmeticPatchesDialog,
        export_dialog=gui.FusionGameExportDialog,
        progressive_item_gui_tuples=(),
        spoiler_visualizer=(HintDetailsTab,),
    )


def _generator() -> randovania.game.generator.GameGenerator:
    from randovania.games.fusion import generator
    from randovania.games.fusion.generator.hint_distributor import FusionHintDistributor
    from randovania.generator.filler.weights import ActionWeights

    return randovania.game.generator.GameGenerator(
        pickup_pool_creator=generator.pool_creator,
        bootstrap=generator.FusionBootstrap(),
        base_patches_factory=generator.FusionBasePatchesFactory(),
        hint_distributor=FusionHintDistributor(),
        action_weights=ActionWeights(events_weight=0.75, hints_weight=0.5),
    )


def _patch_data_factory() -> type[PatchDataFactory]:
    from randovania.games.fusion.exporter.patch_data_factory import FusionPatchDataFactory

    return FusionPatchDataFactory


def _exporter() -> GameExporter:
    from randovania.games.fusion.exporter.game_exporter import FusionGameExporter

    return FusionGameExporter()


def _hash_words() -> list[str]:
    from randovania.games.fusion.hash_words import HASH_WORDS

    return HASH_WORDS


game_data: randovania.game.data.GameData = randovania.game.data.GameData(
    short_name="Fusion",
    long_name="Metroid Fusion",
    development_state=randovania.game.development_state.DevelopmentState.STAGING,
    presets=[
        {"path": "starter_preset.rdvpreset"},
    ],
    faq=[
        (
            "What patcher does Randovania use?",
            "Randovania supports the open source patcher MARS (Metroid Advance Randomizer System). "
            "This is a new patcher built from scratch and is unrelated to other Fusion Randomizers. "
            "Any differences from the vanilla game are covered under the differences tab.",
        ),
        (
            "Which versions of Fusion are supported?",
            "Only the USA version of Fusion is supported with no current plans to support additional versions.",
        ),
        (
            "I saved in a place I can't get out of, am I softlocked?",
            'You can use the "Warp to Start" function in the pause menu by pressing L and confirming. '
            "This will place you back at your start location with everything collected since your last save. "
            "Please note that this is never logical.",
        ),
        (
            "What is required to trigger and fight the SA-X?",
            "To trigger the SA-X fight, you must have collected enough Infant Metroids and approach "
            "the Operations Room hatch. To fight the SA-X you will require Charge Beam and Missiles.\n"
            "Reminder that the Operations Room hatch is now a grey Level 0 hatch.",
        ),
        (
            "How do the Missile Upgrades interact?",
            "The missile upgrades functions have been split, allowing unique combinations of effects and damage.\n"
            "- Missile Launcher Data - Allows Samus to fire missiles causing 10 damage with no other upgrades\n"
            "- Super Missile Data - Adds 20 damage\n"
            "- Ice Missile Data - Adds the ability to freeze enemies with direct hits and adds 10 damage\n"
            "- Diffusion Missile Data - Adds the ability to charge a freezing blast and adds 5 damage",
        ),
        (
            "How do the Beam Upgrades interact?",
            "The beam upgrades have been split, allowing unique combinations of effects and damage.\n"
            "- Charge Beam - Adds the ability to charge Samus' beam and a minor damage increase\n"
            "- Wide Beam - Makes the beam fire 3 projectiles and a major increase to damage\n"
            "- Plasma Beam - Adds the ability to penetrate enemies and a minor damage increase\n"
            "- Wave Beam - Makes the beam fire 2 projectiles and a major damage increase\n"
            "- Ice Beam - Adds the ability to freeze enemies with the beam and a minor damage increase",
        ),
    ],
    hash_words=_hash_words(),
    layout=randovania.game.layout.GameLayout(
        configuration=layout.FusionConfiguration,
        cosmetic_patches=layout.FusionCosmeticPatches,
        preset_describer=FusionPresetDescriber(),
    ),
    options=_options,
    gui=_gui,
    generator=_generator,
    patch_data_factory=_patch_data_factory,
    exporter=_exporter,
    multiple_start_nodes_per_area=True,
    logic_db_integrity=find_fusion_db_errors,
)
