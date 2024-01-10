from __future__ import annotations

from typing import TYPE_CHECKING

import randovania
from randovania.games import game
from randovania.games.planets_zebeth import layout
from randovania.layout.preset_describer import GamePresetDescriber

if TYPE_CHECKING:
    from randovania.games.planets_zebeth.exporter.game_exporter import PlanetsZebethGameExporter
    from randovania.games.planets_zebeth.exporter.options import PlanetsZebethPerGameOptions
    from randovania.games.planets_zebeth.exporter.patch_data_factory import PlanetsZebethPatchDataFactory


def _options() -> type[PlanetsZebethPerGameOptions]:
    from randovania.games.planets_zebeth.exporter.options import PlanetsZebethPerGameOptions

    return PlanetsZebethPerGameOptions


def _gui() -> game.GameGui:
    from randovania.games.planets_zebeth import gui

    return game.GameGui(
        game_tab=gui.PlanetsZebethGameTabWidget,
        tab_provider=gui.preset_tabs,
        cosmetic_dialog=gui.PlanetsZebethCosmeticPatchesDialog,
        export_dialog=gui.PlanetsZebethGameExportDialog,
        progressive_item_gui_tuples=(),
        spoiler_visualizer=(),
    )


def _generator() -> game.GameGenerator:
    from randovania.games.planets_zebeth import generator
    from randovania.generator.hint_distributor import AllJokesHintDistributor

    return game.GameGenerator(
        pickup_pool_creator=generator.pool_creator,
        bootstrap=generator.PlanetsZebethBootstrap(),
        base_patches_factory=generator.PlanetsZebethBasePatchesFactory(),
        hint_distributor=AllJokesHintDistributor(),
    )


def _patch_data_factory() -> type[PlanetsZebethPatchDataFactory]:
    from randovania.games.planets_zebeth.exporter.patch_data_factory import PlanetsZebethPatchDataFactory

    return PlanetsZebethPatchDataFactory


def _exporter() -> PlanetsZebethGameExporter:
    from randovania.games.planets_zebeth.exporter.game_exporter import PlanetsZebethGameExporter

    return PlanetsZebethGameExporter()


game_data: game.GameData = game.GameData(
    short_name="Planets Zebeth",
    long_name="Metroid Planets (Zebeth)",
    development_state=game.DevelopmentState.EXPERIMENTAL,
    presets=[
        {"path": "starter_preset.rdvpreset"},
    ],
    faq=[
        (
            "Which versions of Metroid Planets are supported?",
            "Only version 1.27g is supported. "
            "Later versions are embedding code in the executable "
            "which prevents modifying the code.",
        )
    ],
    layout=game.GameLayout(
        configuration=layout.PlanetsZebethConfiguration,
        cosmetic_patches=layout.PlanetsZebethCosmeticPatches,
        preset_describer=GamePresetDescriber(),
    ),
    options=_options,
    gui=_gui,
    generator=_generator,
    patch_data_factory=_patch_data_factory,
    exporter=_exporter,
    multiple_start_nodes_per_area=False,
    defaults_available_in_game_sessions=randovania.is_dev_version(),
)
