from randovania.games.blank.gui.dialog.cosmetic_patches_dialog import BlankCosmeticPatchesDialog
from randovania.games.blank.layout import BlankCosmeticPatches


def test_reset(skip_qtbot):
    # Setup
    patches = BlankCosmeticPatches()

    dialog = BlankCosmeticPatchesDialog(None, patches)
    skip_qtbot.addWidget(dialog)

    # Run
    dialog.reset()

    # Assert
    assert dialog.cosmetic_patches == patches
