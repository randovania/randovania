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
from randovania.games.prime2_dev import layout

if typing.TYPE_CHECKING:
    from randovania.exporter.game_exporter import GameExporter
    from randovania.exporter.patch_data_factory import PatchDataFactory
    from randovania.interface_common.options import PerGameOptions


def _options() -> type[PerGameOptions]:
    from randovania.games.prime2_dev.exporter.options import EchoesPerGameOptions

    return EchoesPerGameOptions


def _gui() -> randovania.game.gui.GameGui:
    from randovania.games.common.prime_family.gui.prime_trilogy_teleporter_details_tab import (
        PrimeTrilogyTeleporterDetailsTab,
    )
    from randovania.games.prime2_dev import gui
    from randovania.games.prime2_dev.layout import progressive_items
    from randovania.gui.game_details.hint_details_tab import HintDetailsTab

    return randovania.game.gui.GameGui(
        game_tab=gui.EchoesGameTabWidget,
        tab_provider=gui.preset_tabs,
        cosmetic_dialog=gui.EchoesCosmeticPatchesDialog,
        export_dialog=gui.EchoesGameExportDialog,
        progressive_item_gui_tuples=progressive_items.tuples(),
        spoiler_visualizer=(
            PrimeTrilogyTeleporterDetailsTab,
            gui.TranslatorGateDetailsTab,
            HintDetailsTab,
        ),
    )


def _generator() -> randovania.game.generator.GameGenerator:
    from randovania.games.prime2_dev import generator
    from randovania.generator.filler.weights import ActionWeights

    return randovania.game.generator.GameGenerator(
        pickup_pool_creator=generator.pool_creator,
        bootstrap=generator.EchoesBootstrap(),
        base_patches_factory=generator.EchoesBasePatchesFactory(),
        action_weights=ActionWeights(),
    )


def _hints() -> randovania.game.hints.GameHints:
    from randovania.games.prime2_dev import generator

    return randovania.game.hints.GameHints(
        hint_distributor=generator.EchoesHintDistributor(),
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
    from randovania.games.prime2_dev.exporter.patch_data_factory import EchoesPatchDataFactory

    return EchoesPatchDataFactory


def _exporter() -> GameExporter:
    from randovania.games.prime2_dev.exporter.game_exporter import EchoesGameExporter

    return EchoesGameExporter()


def _hash_words() -> list[str]:
    from randovania.games.prime2_dev.hash_words import HASH_WORDS

    return HASH_WORDS


def _test_data() -> randovania.game.game_test_data.GameTestData:
    return randovania.game.game_test_data.GameTestData(
        expected_seed_hash="EQMVN3EN",
        database_collectable_ignore_events=("Event92", "Event97"),
    )


game_data: randovania.game.data.GameData = randovania.game.data.GameData(
    short_name="Echoes",
    long_name="Metroid Prime 2: Echoes (Development)",
    development_state=randovania.game.development_state.DevelopmentState.SOURCE_ONLY,
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
        configuration=layout.EchoesConfiguration,
        cosmetic_patches=layout.EchoesCosmeticPatches,
        preset_describer=layout.EchoesPresetDescriber(),
    ),
    options=_options,
    gui=_gui,
    generator=_generator,
    hints=_hints,
    patch_data_factory=_patch_data_factory,
    exporter=_exporter,
    test_data=_test_data,
    multiple_start_nodes_per_area=False,
)
