import dataclasses
from PySide2.QtCore import QSize
from PySide2.QtGui import QColor

from PySide2.QtWidgets import QColorDialog, QFrame, QLayout, QSizePolicy, QWidget

from randovania.gui.dialog.base_cosmetic_patches_dialog import BaseCosmeticPatchesDialog
from randovania.gui.generated.prime_cosmetic_patches_dialog_ui import Ui_PrimeCosmeticPatchesDialog
from randovania.games.prime1.layout.prime_cosmetic_patches import PrimeCosmeticPatches

SUIT_DEFAULT_COLORS = [
    [ (255, 173, 50), (220, 25, 45), (132, 240, 60) ], # Power
    [ (255, 173, 50), (220, 25, 45), (255, 125, 50), (132, 240, 60) ], # Varia
    [ (170, 170, 145), (70, 25, 50), (40, 20, 90), (140, 240, 240) ], # Gravity
    [ (50, 50, 50), (20, 20, 20), (230, 50, 62) ] # Phazon
]

def hue_rotate_color(original_color: tuple[int,int,int], rotation: int):
    color = QColor.fromRgb(*original_color)
    h = color.hue() + rotation
    s = color.saturation()
    v = color.value()
    while h >= 360:
        h -= 360
    while h < 0:
        h += 360

    rotated_color = QColor.fromHsv(h, s, v)
    return (rotated_color.red(), rotated_color.green(), rotated_color.blue())


class PrimeCosmeticPatchesDialog(BaseCosmeticPatchesDialog, Ui_PrimeCosmeticPatchesDialog):
    _cosmetic_patches: PrimeCosmeticPatches

    def __init__(self, parent: QWidget, current: PrimeCosmeticPatches):
        super().__init__(parent)
        self.setupUi(self)
        self._cosmetic_patches = current

        # Build dynamically preview color squares for suits
        suit_layouts = [ 
            self.power_suit_color_layout, self.varia_suit_color_layout, 
            self.gravity_suit_color_layout, self.phazon_suit_color_layout
        ]
        self.suit_color_preview_squares = []
        for suit_layout, suit_colors in zip(suit_layouts, SUIT_DEFAULT_COLORS):
            self.suit_color_preview_squares.append([
                self._add_preview_color_square_to_layout(suit_layout, color)
                for color in suit_colors
            ])

        self.on_new_cosmetic_patches(current)
        self.connect_signals()

        self._update_color_squares()

    def connect_signals(self):
        super().connect_signals()

        self.qol_cosmetic_check.stateChanged.connect(self._persist_option_then_notify("qol_cosmetic"))
        self.open_map_check.stateChanged.connect(self._persist_option_then_notify("open_map"))
        self.custom_hud_color.stateChanged.connect(self._persist_option_then_notify("use_hud_color"))
        self.power_suit_rotation_field.valueChanged.connect(self._persist_suit_color_rotations)
        self.varia_suit_rotation_field.valueChanged.connect(self._persist_suit_color_rotations)
        self.gravity_suit_rotation_field.valueChanged.connect(self._persist_suit_color_rotations)
        self.phazon_suit_rotation_field.valueChanged.connect(self._persist_suit_color_rotations)
        self.custom_hud_color_button.clicked.connect(self._open_color_picker)

    def on_new_cosmetic_patches(self, patches: PrimeCosmeticPatches):
        self.qol_cosmetic_check.setChecked(patches.qol_cosmetic)
        self.open_map_check.setChecked(patches.open_map)
        self.custom_hud_color.setChecked(patches.use_hud_color)
        self.power_suit_rotation_field.setValue(patches.suit_color_rotations[0])
        self.varia_suit_rotation_field.setValue(patches.suit_color_rotations[1])
        self.gravity_suit_rotation_field.setValue(patches.suit_color_rotations[2])
        self.phazon_suit_rotation_field.setValue(patches.suit_color_rotations[3])

    def _persist_option_then_notify(self, attribute_name: str):
        def persist(value: int):
            self._cosmetic_patches = dataclasses.replace(
                self._cosmetic_patches,
                **{attribute_name: bool(value)}
            )

        return persist

    def _persist_suit_color_rotations(self):
        suit_color_rotations_tuple=(
            self.power_suit_rotation_field.value(),
            self.varia_suit_rotation_field.value(),
            self.gravity_suit_rotation_field.value(),
            self.phazon_suit_rotation_field.value()
        )
        self._cosmetic_patches = dataclasses.replace(self._cosmetic_patches, suit_color_rotations=suit_color_rotations_tuple)
        self._update_color_squares()

    def _open_color_picker(self):
        init_color = self._cosmetic_patches.hud_color
        color = QColorDialog.getColor(QColor(*init_color))
        
        if color.isValid():
            color_tuple = (color.red(), color.green(), color.blue())
            self._cosmetic_patches = dataclasses.replace(self._cosmetic_patches, hud_color=color_tuple)
            self._update_color_squares()

    def _update_color_squares(self):
        color = self._cosmetic_patches.hud_color
        style = 'background-color: rgb({},{},{})'.format(*color)
        self.custom_hud_color_square.setStyleSheet(style)

        for i, suit_colors in enumerate(SUIT_DEFAULT_COLORS):
            for j, color in enumerate(suit_colors):
                color = hue_rotate_color(color, self._cosmetic_patches.suit_color_rotations[i])
                style = 'background-color: rgb({},{},{})'.format(*color)
                self.suit_color_preview_squares[i][j].setStyleSheet(style)

    def _add_preview_color_square_to_layout(self, layout: QLayout, default_color: tuple[int,int,int]):
        color_square = QFrame(self.game_changes_box)
        color_square.setMinimumSize(QSize(22, 22))
        color_square.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        color_square.setStyleSheet('background-color: rgb({},{},{})'.format(*default_color))
        layout.addWidget(color_square)
        return color_square

    @property
    def cosmetic_patches(self) -> PrimeCosmeticPatches:
        return self._cosmetic_patches

    def reset(self):
        self.on_new_cosmetic_patches(PrimeCosmeticPatches())
