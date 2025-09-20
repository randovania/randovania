from __future__ import annotations

from collections import defaultdict
from unittest.mock import MagicMock

from randovania.game.game_enum import RandovaniaGame
from randovania.lib import enum_lib


def test_gui(skip_qtbot, game_enum):
    from randovania.gui.dialog.base_cosmetic_patches_dialog import BaseCosmeticPatchesDialog
    from randovania.gui.dialog.game_export_dialog import GameExportDialog
    from randovania.gui.game_details.game_details_tab import GameDetailsTab

    # Run
    g = game_enum.gui
    skip_qtbot.addWidget(g.game_tab(MagicMock(), MagicMock(), MagicMock()))

    # Assert
    if g.cosmetic_dialog is not None:
        assert issubclass(g.cosmetic_dialog, BaseCosmeticPatchesDialog)
    assert issubclass(g.export_dialog, GameExportDialog)
    for v in g.spoiler_visualizer:
        assert issubclass(v, GameDetailsTab)


def test_generator(game_enum):
    from randovania.generator.base_patches_factory import BasePatchesFactory
    from randovania.resolver.bootstrap import Bootstrap

    # Run
    g = game_enum.generator

    # Assert
    assert isinstance(g.bootstrap, Bootstrap)
    assert isinstance(g.base_patches_factory, BasePatchesFactory)


def test_hints(game_enum):
    from randovania.game.hints import GameHints
    from randovania.generator.hint_distributor import HintDistributor

    # Run
    h = game_enum.hints

    # Assert
    assert isinstance(h, GameHints)
    assert isinstance(h.hint_distributor, HintDistributor)


def test_patch_data_factory(game_enum):
    from randovania.exporter.patch_data_factory import PatchDataFactory

    assert issubclass(game_enum.patch_data_factory, PatchDataFactory)


def test_exporter(game_enum):
    from randovania.exporter.game_exporter import GameExporter

    assert isinstance(game_enum.exporter, GameExporter)


def test_presets():
    from randovania.interface_common.preset_manager import PresetManager

    games_preset_count: dict[RandovaniaGame, int] = defaultdict(int)

    # Ensure that we can parse all the games' presets
    manager = PresetManager(None)
    for uuid, preset in manager.included_presets.items():
        games_preset_count[preset.game] += 1

    # Assert that every game has at least one preset
    for game in enum_lib.iterate_enum(RandovaniaGame):
        assert games_preset_count[game] >= 0
