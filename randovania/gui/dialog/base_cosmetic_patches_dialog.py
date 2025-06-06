from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from PySide6 import QtWidgets

from randovania.gui.lib import signal_handling

if TYPE_CHECKING:
    from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches


class BaseCosmeticPatchesDialog[CosmeticPatches: BaseCosmeticPatches](QtWidgets.QDialog):
    _cosmetic_patches: CosmeticPatches
    accept_button: QtWidgets.QPushButton
    cancel_button: QtWidgets.QPushButton
    reset_button: QtWidgets.QPushButton

    def __init__(self, parent: QtWidgets.QWidget | None, current: CosmeticPatches):
        super().__init__(parent)
        assert isinstance(current, self.cosmetic_patches_type())
        self._cosmetic_patches = current

    @classmethod
    def cosmetic_patches_type(cls) -> type[CosmeticPatches]:
        raise NotImplementedError

    def connect_signals(self) -> None:
        self.accept_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        self.reset_button.clicked.connect(self.reset)

    def reset(self) -> None:
        raise NotImplementedError

    @property
    def cosmetic_patches(self) -> CosmeticPatches:
        raise NotImplementedError

    def _persist_check_field(self, check: QtWidgets.QCheckBox, attribute_name: str) -> None:
        def persist_field(value: bool) -> None:
            self._cosmetic_patches = dataclasses.replace(
                self._cosmetic_patches,
                **{attribute_name: value},
            )

        signal_handling.on_checked(check, persist_field)
