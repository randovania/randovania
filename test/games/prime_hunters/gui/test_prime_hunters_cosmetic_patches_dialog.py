from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from PySide6 import QtCore

from randovania.games.prime_hunters.gui.dialog.cosmetic_patches_dialog import HuntersCosmeticPatchesDialog
from randovania.games.prime_hunters.layout.prime_hunters_cosmetic_patches import HuntersCosmeticPatches

if TYPE_CHECKING:
    from randovania.interface_common.options import Options


@pytest.mark.parametrize(
    ("field_name", "widget_field"),
    [
        ("shuffle_hunter_colors", "shuffle_hunter_colors_check"),
    ],
)
def test_enable_checkboxes(skip_qtbot, field_name: str, widget_field: str, options: Options) -> None:
    cosmetic_patches = HuntersCosmeticPatches(**{field_name: False})  # type: ignore[arg-type]

    dialog = HuntersCosmeticPatchesDialog(None, cosmetic_patches, options)
    skip_qtbot.addWidget(dialog)
    # Run
    skip_qtbot.mouseClick(getattr(dialog, widget_field), QtCore.Qt.MouseButton.LeftButton)
    # Assert
    assert dialog.cosmetic_patches == HuntersCosmeticPatches(**{field_name: True})  # type: ignore[arg-type]
