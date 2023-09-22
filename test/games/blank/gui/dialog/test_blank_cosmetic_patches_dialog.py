from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.blank.gui.dialog.cosmetic_patches_dialog import BlankCosmeticPatchesDialog
from randovania.games.blank.layout import BlankCosmeticPatches

if TYPE_CHECKING:
    import pytestqt.qtbot  # type: ignore[import]


def test_reset(skip_qtbot: pytestqt.qtbot.QtBot) -> None:
    # Setup
    patches = BlankCosmeticPatches()

    dialog = BlankCosmeticPatchesDialog(None, patches)
    skip_qtbot.addWidget(dialog)

    # Run
    dialog.reset()

    # Assert
    assert dialog.cosmetic_patches == patches
