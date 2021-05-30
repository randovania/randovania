from PySide2 import QtWidgets

from randovania.games.game import RandovaniaGame
from randovania.gui.dialog.base_cosmetic_patches_dialog import BaseCosmeticPatchesDialog
from randovania.gui.dialog.corruption_cosmetic_patches_dialog import CorruptionCosmeticPatchesDialog
from randovania.gui.dialog.echoes_cosmetic_patches_dialog import EchoesCosmeticPatchesDialog
from randovania.gui.dialog.prime_cosmetic_patches_dialog import PrimeCosmeticPatchesDialog
from randovania.layout.game_to_class import AnyCosmeticPatches

COSMETIC_DIALOG_FOR_GAME = {
    RandovaniaGame.PRIME1: PrimeCosmeticPatchesDialog,
    RandovaniaGame.PRIME2: EchoesCosmeticPatchesDialog,
    RandovaniaGame.PRIME3: CorruptionCosmeticPatchesDialog,
}


def create_dialog_for_cosmetic_patches(
        parent: QtWidgets.QWidget,
        initial_patches: AnyCosmeticPatches,
) -> BaseCosmeticPatchesDialog:
    game = initial_patches.game()
    dialog_class = COSMETIC_DIALOG_FOR_GAME[game]
    return dialog_class(parent, initial_patches)
