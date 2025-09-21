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
from randovania.games.blank import layout
from randovania.layout.preset_describer import GamePresetDescriber

if typing.TYPE_CHECKING:
    from randovania.exporter.game_exporter import GameExporter
    from randovania.exporter.patch_data_factory import PatchDataFactory
    from randovania.interface_common.options import PerGameOptions


def _options() -> type[PerGameOptions]:
    from randovania.games.blank.exporter.options import BlankPerGameOptions

    return BlankPerGameOptions


def _gui() -> randovania.game.gui.GameGui:
    from randovania.games.blank import gui
    from randovania.games.blank.layout import progressive_items
    from randovania.gui.game_details.hint_details_tab import HintDetailsTab

    return randovania.game.gui.GameGui(
        game_tab=gui.BlankGameTabWidget,
        tab_provider=gui.preset_tabs,
        cosmetic_dialog=gui.BlankCosmeticPatchesDialog,
        export_dialog=gui.BlankGameExportDialog,
        progressive_item_gui_tuples=progressive_items.tuples(),
        spoiler_visualizer=(HintDetailsTab,),
    )


def _generator() -> randovania.game.generator.GameGenerator:
    from randovania.games.blank import generator
    from randovania.generator.filler.weights import ActionWeights

    return randovania.game.generator.GameGenerator(
        pickup_pool_creator=generator.pool_creator,
        bootstrap=generator.BlankBootstrap(),
        base_patches_factory=generator.BlankBasePatchesFactory(),
        action_weights=ActionWeights(),
    )


def _hints() -> randovania.game.hints.GameHints:
    from randovania.games.blank import generator

    return randovania.game.hints.GameHints(
        hint_distributor=generator.BlankHintDistributor(),
        specific_pickup_hints={},
    )


def _patch_data_factory() -> type[PatchDataFactory]:
    from randovania.games.blank.exporter.patch_data_factory import BlankPatchDataFactory

    return BlankPatchDataFactory


def _exporter() -> GameExporter:
    from randovania.games.blank.exporter.game_exporter import BlankGameExporter

    return BlankGameExporter()


def _hash_words() -> list[str]:
    from randovania.games.blank.hash_words import HASH_WORDS

    return HASH_WORDS


game_data: randovania.game.data.GameData = randovania.game.data.GameData(
    short_name="Blank",
    long_name="Blank Development Game",
    development_state=randovania.game.development_state.DevelopmentState.STAGING,
    presets=["starter_preset.rdvpreset"],
    faq=[],
    web_info=randovania.game.web_info.GameWebInfo(
        what_can_randomize=(
            "Everything",
            "Nothing",
        ),
        need_to_play=(
            "A Nintendo Virtual Boy",
            "Your original Virtual Boy Game Cartridge",
        ),
    ),
    hash_words=_hash_words(),
    layout=randovania.game.layout.GameLayout(
        configuration=layout.BlankConfiguration,
        cosmetic_patches=layout.BlankCosmeticPatches,
        preset_describer=GamePresetDescriber(),
    ),
    options=_options,
    gui=_gui,
    generator=_generator,
    hints=_hints,
    patch_data_factory=_patch_data_factory,
    exporter=_exporter,
    multiple_start_nodes_per_area=True,
    defaults_available_in_game_sessions=randovania.is_dev_version(),
)
