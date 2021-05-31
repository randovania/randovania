from PySide2 import QtCore

from randovania.gui.dialog.corruption_cosmetic_patches_dialog import CorruptionCosmeticPatchesDialog
from randovania.gui.dialog.echoes_cosmetic_patches_dialog import EchoesCosmeticPatchesDialog
from randovania.gui.dialog.prime_cosmetic_patches_dialog import PrimeCosmeticPatchesDialog
from randovania.layout.prime1.prime_cosmetic_patches import PrimeCosmeticPatches
from randovania.layout.prime2.echoes_cosmetic_patches import EchoesCosmeticPatches
from randovania.layout.prime2.echoes_user_preferences import EchoesUserPreferences, SoundMode
from randovania.layout.prime3.corruption_cosmetic_patches import CorruptionCosmeticPatches, CorruptionSuit


def test_random_welding_colors(skip_qtbot):
    cosmetic_patches = CorruptionCosmeticPatches(random_welding_colors=False)

    dialog = CorruptionCosmeticPatchesDialog(None, cosmetic_patches)
    skip_qtbot.addWidget(dialog)

    skip_qtbot.mouseClick(dialog.random_welding_colors_check, QtCore.Qt.LeftButton)

    assert dialog.cosmetic_patches == CorruptionCosmeticPatches(random_welding_colors=True)


def test_open_map(skip_qtbot):
    cosmetic_patches = CorruptionCosmeticPatches(player_suit=CorruptionSuit.CORRUPTED_25)

    dialog = CorruptionCosmeticPatchesDialog(None, cosmetic_patches)
    skip_qtbot.addWidget(dialog)

    skip_qtbot.keyClicks(dialog.suit_combo, "PED")

    assert dialog.cosmetic_patches == CorruptionCosmeticPatches(player_suit=CorruptionSuit.PED)
