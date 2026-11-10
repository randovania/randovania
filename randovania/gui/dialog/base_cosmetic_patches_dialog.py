from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from PySide6 import QtWidgets

from randovania.gui.generated.base_cosmetic_patches_dialog_base_ui import Ui_BaseCosmeticPatchesDialog
from randovania.gui.lib import signal_handling

if TYPE_CHECKING:
    from randovania.interface_common.options import Options
    from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches


class GameSpecificCosmeticWidget[CosmeticPatches: BaseCosmeticPatches](QtWidgets.QWidget):
    _cosmetic_patches: CosmeticPatches

    def __init__(self, parent: QtWidgets.QWidget | None, current: CosmeticPatches, options: Options) -> None:
        super().__init__(parent)
        self._cosmetic_patches = current

    def reset(self) -> None:
        raise NotImplementedError

    @classmethod
    def cosmetic_patches_type(cls) -> type[BaseCosmeticPatches]:
        raise NotImplementedError

    @property
    def cosmetic_patches(self) -> CosmeticPatches:
        return self._cosmetic_patches

    def default_size(self) -> tuple[int, int]:
        geometry = self.geometry()
        return geometry.width(), geometry.height()

    def _persist_check_field(self, check: QtWidgets.QCheckBox, attribute_name: str) -> None:
        def persist_field(value: bool) -> None:
            self._cosmetic_patches = dataclasses.replace(
                self._cosmetic_patches,
                **{attribute_name: value},
            )

        signal_handling.on_checked(check, persist_field)


class BaseCosmeticPatchesDialog[CosmeticPatches: BaseCosmeticPatches](QtWidgets.QDialog, Ui_BaseCosmeticPatchesDialog):
    accept_button: QtWidgets.QPushButton
    cancel_button: QtWidgets.QPushButton
    reset_button: QtWidgets.QPushButton
    contentWidget: GameSpecificCosmeticWidget[BaseCosmeticPatches]

    def __init__(
        self,
        parent: QtWidgets.QWidget | None,
        current: CosmeticPatches,
        options: Options,
        game_widget: type[GameSpecificCosmeticWidget],
    ) -> None:
        super().__init__(parent)
        self.setupUi(self)
        assert isinstance(current, game_widget.cosmetic_patches_type())

        widget = game_widget(self.scroll_area_contents, current, options)
        self.scroll_area_layout.replaceWidget(self.contentWidget, widget)
        geometry = self.geometry()
        default_width, default_height = widget.default_size()
        geometry.setWidth(default_width)
        geometry.setHeight(default_height)
        self.setGeometry(geometry)
        self.setWindowTitle(f"{widget.cosmetic_patches.game().long_name} - Cosmetic Options")

        self.contentWidget = widget

        self.connect_signals()

    def connect_signals(self) -> None:
        self.accept_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        self.reset_button.clicked.connect(self.reset)

    def reset(self) -> None:
        self.contentWidget.reset()

    @property
    def cosmetic_patches(self) -> CosmeticPatches:
        return self.contentWidget.cosmetic_patches
