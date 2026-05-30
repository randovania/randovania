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
from randovania.layout.preset_describer import GamePresetDescriber

if typing.TYPE_CHECKING:
    from randovania.exporter.game_exporter import GameExporter
    from randovania.exporter.patch_data_factory import PatchDataFactory
    from randovania.interface_common.options import PerGameOptions


def _options() -> type[PerGameOptions]:
    from randovania.games.prime2_opr.exporter.options import EchoesOPRPerGameOptions

    return EchoesOPRPerGameOptions


def _gui() -> randovania.game.gui.GameGui:
    from randovania.games.prime2_opr import gui
    from randovania.games.prime2_opr.layout import progressive_items
    from randovania.gui.game_details.hint_details_tab import HintDetailsTab

    return randovania.game.gui.GameGui(
        game_tab=gui.EchoesOPRGameTabWidget,
        tab_provider=gui.preset_tabs,
        cosmetic_dialog=gui.EchoesOPRCosmeticPatchesDialog,
        export_dialog=gui.EchoesOPRGameExportDialog,
        progressive_item_gui_tuples=progressive_items.tuples(),
        spoiler_visualizer=(HintDetailsTab,),
    )


def _generator() -> randovania.game.generator.GameGenerator:
    from randovania.games.prime2_opr import generator
    from randovania.generator.filler.weights import ActionWeights

    return randovania.game.generator.GameGenerator(
        pickup_pool_creator=generator.pool_creator,
        bootstrap=generator.EchoesOPRBootstrap(),
        base_patches_factory=generator.EchoesOPRBasePatchesFactory(),
        action_weights=ActionWeights(),
    )


def _hints() -> randovania.game.hints.GameHints:
    from randovania.games.prime2_opr import generator

    return randovania.game.hints.GameHints(
        hint_distributor=generator.EchoesOPRHintDistributor(),
        specific_pickup_hints={},
    )


def _patch_data_factory() -> type[PatchDataFactory]:
    from randovania.games.prime2_opr.exporter.patch_data_factory import EchoesOPRPatchDataFactory

    return EchoesOPRPatchDataFactory


def _exporter() -> GameExporter:
    from randovania.games.prime2_opr.exporter.game_exporter import EchoesOPRGameExporter

    return EchoesOPRGameExporter()


def _hash_words() -> list[str]:
    from randovania.games.prime2_opr.hash_words import HASH_WORDS

    return HASH_WORDS


def _test_data() -> randovania.game.game_test_data.GameTestData:
    return randovania.game.game_test_data.GameTestData(
        expected_seed_hash="O4DMH5PE",
    )


game_data: randovania.game.data.GameData = randovania.game.data.GameData(
    short_name="EchoesOPR",
    long_name="Metroid Prime 2: Echoes (Open Prime Rando)",
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
        configuration=layout.EchoesOPRConfiguration,
        cosmetic_patches=layout.EchoesOPRCosmeticPatches,
        preset_describer=GamePresetDescriber(),
    ),
    options=_options,
    gui=_gui,
    generator=_generator,
    hints=_hints,
    patch_data_factory=_patch_data_factory,
    exporter=_exporter,
    test_data=_test_data,
    multiple_start_nodes_per_area=True,
)
