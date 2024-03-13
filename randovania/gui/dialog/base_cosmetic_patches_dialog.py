from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from PySide6 import QtWidgets

from randovania.gui.lib import signal_handling

if TYPE_CHECKING:
    from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches


class BaseCosmeticPatchesDialog(QtWidgets.QDialog):
    _cosmetic_patches: BaseCosmeticPatches
    accept_button: QtWidgets.QPushButton
    cancel_button: QtWidgets.QPushButton
    reset_button: QtWidgets.QPushButton

    def connect_signals(self) -> None:
        self.accept_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        self.reset_button.clicked.connect(self.reset)

    def reset(self) -> None:
        raise NotImplementedError

    @property
    def cosmetic_patches(self) -> BaseCosmeticPatches:
        raise NotImplementedError

    def _persist_check_field(self, check: QtWidgets.QCheckBox, attribute_name: str) -> None:
        def persist_field(value: bool) -> None:
            self._cosmetic_patches = dataclasses.replace(
                self._cosmetic_patches,
                **{attribute_name: value},  # type: ignore[arg-type]
            )

        signal_handling.on_checked(check, persist_field)
