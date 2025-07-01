from __future__ import annotations

import typing

import randovania
import randovania.game.data
import randovania.game.development_state
import randovania.game.generator
import randovania.game.gui
import randovania.game.hints
import randovania.game.layout
import randovania.game.web_info
from randovania.games.pseudoregalia import layout
from randovania.games.pseudoregalia.layout.preset_describer import PseudoregaliaPresetDescriber

if typing.TYPE_CHECKING:
    from randovania.exporter.game_exporter import GameExporter
    from randovania.exporter.patch_data_factory import PatchDataFactory
    from randovania.interface_common.options import PerGameOptions


def _options() -> type[PerGameOptions]:
    from randovania.games.pseudoregalia.exporter.options import PseudoregaliaPerGameOptions

    return PseudoregaliaPerGameOptions


def _gui() -> randovania.game.gui.GameGui:
    from randovania.games.pseudoregalia import gui
    from randovania.games.pseudoregalia.layout import progressive_items
    from randovania.gui.game_details.hint_details_tab import HintDetailsTab

    return randovania.game.gui.GameGui(
        game_tab=gui.PseudoregaliaGameTabWidget,
        tab_provider=gui.preset_tabs,
        cosmetic_dialog=gui.PseudoregaliaCosmeticPatchesDialog,
        export_dialog=gui.PseudoregaliaGameExportDialog,
        progressive_item_gui_tuples=progressive_items.tuples(),
        spoiler_visualizer=(HintDetailsTab,),
    )


def _generator() -> randovania.game.generator.GameGenerator:
    from randovania.games.pseudoregalia import generator
    from randovania.generator.filler.weights import ActionWeights

    return randovania.game.generator.GameGenerator(
        pickup_pool_creator=generator.pool_creator,
        bootstrap=generator.PseudoregaliaBootstrap(),
        base_patches_factory=generator.PseudoregaliaBasePatchesFactory(),
        action_weights=ActionWeights(),
    )


def _hints() -> randovania.game.hints.GameHints:
    from randovania.games.pseudoregalia import generator

    return randovania.game.hints.GameHints(
        hint_distributor=generator.PseudoregaliaHintDistributor(),
        specific_pickup_hints={
            "major_keys": randovania.game.hints.SpecificHintDetails(
                long_name="Major Keys",
                description="This controls how precise the hints in Tower Remains are for Major Keys.",
            )
        },
    )


def _patch_data_factory() -> type[PatchDataFactory]:
    from randovania.games.pseudoregalia.exporter.patch_data_factory import PseudoregaliaPatchDataFactory

    return PseudoregaliaPatchDataFactory


def _exporter() -> GameExporter:
    from randovania.games.pseudoregalia.exporter.game_exporter import PseudoregaliaGameExporter

    return PseudoregaliaGameExporter()


def _hash_words() -> list[str]:
    from randovania.games.pseudoregalia.hash_words import HASH_WORDS

    return HASH_WORDS


game_data: randovania.game.data.GameData = randovania.game.data.GameData(
    short_name="Pseudoregalia",
    long_name="Pseudoregalia",
    development_state=randovania.game.development_state.DevelopmentState.STAGING,
    presets=[
        {"path": "starter_preset.rdvpreset"},
    ],
    faq=[],
    web_info=randovania.game.web_info.GameWebInfo(
        what_can_randomize=(),
        need_to_play=(),
    ),
    hash_words=_hash_words(),
    layout=randovania.game.layout.GameLayout(
        configuration=layout.PseudoregaliaConfiguration,
        cosmetic_patches=layout.PseudoregaliaCosmeticPatches,
        preset_describer=PseudoregaliaPresetDescriber(),
    ),
    options=_options,
    gui=_gui,
    generator=_generator,
    hints=_hints,
    patch_data_factory=_patch_data_factory,
    exporter=_exporter,
    multiple_start_nodes_per_area=True,
)
