from PySide6.QtWidgets import QDialog

from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches


class BaseCosmeticPatchesDialog(QDialog):
    def connect_signals(self):
        self.accept_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        self.reset_button.clicked.connect(self.reset)

    def reset(self):
        raise NotImplementedError()

    @property
    def cosmetic_patches(self) -> BaseCosmeticPatches:
        raise NotImplementedError()
