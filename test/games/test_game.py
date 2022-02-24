def test_gui(skip_qtbot, game_enum):
    from randovania.gui.dialog.base_cosmetic_patches_dialog import BaseCosmeticPatchesDialog
    from randovania.gui.dialog.game_export_dialog import GameExportDialog
    from randovania.gui.game_details.game_details_tab import GameDetailsTab

    # Run
    g = game_enum.gui
    if g.help_widget is not None:
        skip_qtbot.addWidget(g.help_widget())

    # Assert
    assert issubclass(g.cosmetic_dialog, BaseCosmeticPatchesDialog)
    assert issubclass(g.export_dialog, GameExportDialog)
    for v in g.spoiler_visualizer:
        assert issubclass(v, GameDetailsTab)


def test_generator(game_enum):
    from randovania.resolver.bootstrap import Bootstrap
    from randovania.generator.base_patches_factory import BasePatchesFactory
    from randovania.generator.hint_distributor import HintDistributor

    # Run
    g = game_enum.generator

    # Assert
    assert isinstance(g.bootstrap, Bootstrap)
    assert isinstance(g.base_patches_factory, BasePatchesFactory)
    if g.hint_distributor is not None:
        assert isinstance(g.hint_distributor, HintDistributor)


def test_patch_data_factory(game_enum):
    from randovania.exporter.patch_data_factory import BasePatchDataFactory
    assert issubclass(game_enum.patch_data_factory, BasePatchDataFactory)


def test_exporter(game_enum):
    from randovania.exporter.game_exporter import GameExporter
    assert isinstance(game_enum.exporter, GameExporter)
