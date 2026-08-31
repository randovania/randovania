# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'prime_cosmetic_patches_dialog.ui'
##
## Created by: tools/uic_wrapper.py
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog,
    QFrame, QGridLayout, QGroupBox, QHBoxLayout,
    QLabel, QPushButton, QScrollArea, QSizePolicy,
    QSlider, QSpacerItem, QVBoxLayout, QWidget)

from randovania.gui.widgets.foldable import Foldable
from randovania.gui.widgets.scroll_protected import ScrollProtectedSlider

class Ui_PrimeCosmeticPatchesDialog(object):
    def setupUi(self, PrimeCosmeticPatchesDialog):
        if not PrimeCosmeticPatchesDialog.objectName():
            PrimeCosmeticPatchesDialog.setObjectName(u"PrimeCosmeticPatchesDialog")
        PrimeCosmeticPatchesDialog.resize(600, 640)
        self.gridLayout = QGridLayout(PrimeCosmeticPatchesDialog)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setContentsMargins(11, 11, 11, 11)
        self.gridLayout.setObjectName(u"gridLayout")
        self.reset_button = QPushButton(PrimeCosmeticPatchesDialog)
        self.reset_button.setObjectName(u"reset_button")

        self.gridLayout.addWidget(self.reset_button, 2, 2, 1, 1)

        self.accept_button = QPushButton(PrimeCosmeticPatchesDialog)
        self.accept_button.setObjectName(u"accept_button")

        self.gridLayout.addWidget(self.accept_button, 2, 0, 1, 1)

        self.cancel_button = QPushButton(PrimeCosmeticPatchesDialog)
        self.cancel_button.setObjectName(u"cancel_button")

        self.gridLayout.addWidget(self.cancel_button, 2, 1, 1, 1)

        self.scrollArea = QScrollArea(PrimeCosmeticPatchesDialog)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.scroll_area_contents = QWidget()
        self.scroll_area_contents.setObjectName(u"scroll_area_contents")
        self.scroll_area_contents.setGeometry(QRect(0, 0, 566, 1236))
        self.verticalLayout = QVBoxLayout(self.scroll_area_contents)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.game_changes_box = QGroupBox(self.scroll_area_contents)
        self.game_changes_box.setObjectName(u"game_changes_box")
        self.game_changes_layout = QVBoxLayout(self.game_changes_box)
        self.game_changes_layout.setSpacing(6)
        self.game_changes_layout.setContentsMargins(11, 11, 11, 11)
        self.game_changes_layout.setObjectName(u"game_changes_layout")
        self.pickup_markers_check = QCheckBox(self.game_changes_box)
        self.pickup_markers_check.setObjectName(u"pickup_markers_check")

        self.game_changes_layout.addWidget(self.pickup_markers_check)

        self.open_map_check = QCheckBox(self.game_changes_box)
        self.open_map_check.setObjectName(u"open_map_check")

        self.game_changes_layout.addWidget(self.open_map_check)

        self.hud_color_layout = QHBoxLayout()
        self.hud_color_layout.setSpacing(6)
        self.hud_color_layout.setObjectName(u"hud_color_layout")
        self.custom_hud_color = QCheckBox(self.game_changes_box)
        self.custom_hud_color.setObjectName(u"custom_hud_color")

        self.hud_color_layout.addWidget(self.custom_hud_color)

        self.custom_hud_color_button = QPushButton(self.game_changes_box)
        self.custom_hud_color_button.setObjectName(u"custom_hud_color_button")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.custom_hud_color_button.sizePolicy().hasHeightForWidth())
        self.custom_hud_color_button.setSizePolicy(sizePolicy)

        self.hud_color_layout.addWidget(self.custom_hud_color_button)

        self.custom_hud_color_square = QFrame(self.game_changes_box)
        self.custom_hud_color_square.setObjectName(u"custom_hud_color_square")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.custom_hud_color_square.sizePolicy().hasHeightForWidth())
        self.custom_hud_color_square.setSizePolicy(sizePolicy1)
        self.custom_hud_color_square.setMinimumSize(QSize(22, 22))
        self.custom_hud_color_square.setAutoFillBackground(False)
        self.custom_hud_color_square.setFrameShape(QFrame.Shape.StyledPanel)
        self.custom_hud_color_square.setFrameShadow(QFrame.Shadow.Raised)
        self.custom_hud_color_square.setLineWidth(1)

        self.hud_color_layout.addWidget(self.custom_hud_color_square)

        self.hud_color_spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hud_color_layout.addItem(self.hud_color_spacer)


        self.game_changes_layout.addLayout(self.hud_color_layout)


        self.verticalLayout.addWidget(self.game_changes_box)

        self.suit_colors_foldable = Foldable(self.scroll_area_contents)
        self.suit_colors_foldable.setObjectName(u"suit_colors_foldable")
        self.suit_colors_foldable.setProperty(u"folded", False)
        self.suit_colors_foldable_layout = QVBoxLayout(self.suit_colors_foldable)
        self.suit_colors_foldable_layout.setSpacing(6)
        self.suit_colors_foldable_layout.setContentsMargins(11, 11, 11, 11)
        self.suit_colors_foldable_layout.setObjectName(u"suit_colors_foldable_layout")
        self.suit_colors_layout = QGridLayout()
        self.suit_colors_layout.setSpacing(6)
        self.suit_colors_layout.setObjectName(u"suit_colors_layout")
        self.suit_toggles_layout = QVBoxLayout()
        self.suit_toggles_layout.setSpacing(6)
        self.suit_toggles_layout.setObjectName(u"suit_toggles_layout")
        self.force_fusion_check = QCheckBox(self.suit_colors_foldable)
        self.force_fusion_check.setObjectName(u"force_fusion_check")

        self.suit_toggles_layout.addWidget(self.force_fusion_check)

        self.rainbow_phazon_ball_check = QCheckBox(self.suit_colors_foldable)
        self.rainbow_phazon_ball_check.setObjectName(u"rainbow_phazon_ball_check")

        self.suit_toggles_layout.addWidget(self.rainbow_phazon_ball_check)

        self.suit_toggles_spacer = QSpacerItem(20, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.suit_toggles_layout.addItem(self.suit_toggles_spacer)


        self.suit_colors_layout.addLayout(self.suit_toggles_layout, 0, 0, 3, 2)

        self.gunship_header_layout = QHBoxLayout()
        self.gunship_header_layout.setSpacing(6)
        self.gunship_header_layout.setObjectName(u"gunship_header_layout")
        self.gunship_header_left_spacer = QSpacerItem(0, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gunship_header_layout.addItem(self.gunship_header_left_spacer)

        self.gunship_name_label = QLabel(self.suit_colors_foldable)
        self.gunship_name_label.setObjectName(u"gunship_name_label")

        self.gunship_header_layout.addWidget(self.gunship_name_label)

        self.gunship_header_separator_label = QLabel(self.suit_colors_foldable)
        self.gunship_header_separator_label.setObjectName(u"gunship_header_separator_label")

        self.gunship_header_layout.addWidget(self.gunship_header_separator_label)

        self.match_gunship_to_power_suit_check = QCheckBox(self.suit_colors_foldable)
        self.match_gunship_to_power_suit_check.setObjectName(u"match_gunship_to_power_suit_check")

        self.gunship_header_layout.addWidget(self.match_gunship_to_power_suit_check)

        self.gunship_header_right_spacer = QSpacerItem(0, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gunship_header_layout.addItem(self.gunship_header_right_spacer)


        self.suit_colors_layout.addLayout(self.gunship_header_layout, 0, 2, 1, 2)

        self.gunship_slider_layout = QHBoxLayout()
        self.gunship_slider_layout.setSpacing(6)
        self.gunship_slider_layout.setObjectName(u"gunship_slider_layout")
        self.gunship_slider_left_spacer = QSpacerItem(0, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gunship_slider_layout.addItem(self.gunship_slider_left_spacer)

        self.gunship_rotation_slider = ScrollProtectedSlider(self.suit_colors_foldable)
        self.gunship_rotation_slider.setObjectName(u"gunship_rotation_slider")
        sizePolicy1.setHeightForWidth(self.gunship_rotation_slider.sizePolicy().hasHeightForWidth())
        self.gunship_rotation_slider.setSizePolicy(sizePolicy1)
        self.gunship_rotation_slider.setMinimumSize(QSize(180, 0))
        self.gunship_rotation_slider.setMaximumSize(QSize(180, 16777215))
        self.gunship_rotation_slider.setMaximum(360)
        self.gunship_rotation_slider.setSingleStep(5)
        self.gunship_rotation_slider.setPageStep(30)
        self.gunship_rotation_slider.setOrientation(Qt.Orientation.Horizontal)
        self.gunship_rotation_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.gunship_rotation_slider.setTickInterval(90)

        self.gunship_slider_layout.addWidget(self.gunship_rotation_slider)

        self.gunship_slider_right_spacer = QSpacerItem(0, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gunship_slider_layout.addItem(self.gunship_slider_right_spacer)


        self.suit_colors_layout.addLayout(self.gunship_slider_layout, 1, 2, 1, 2)

        self.gunship_image_label = QLabel(self.suit_colors_foldable)
        self.gunship_image_label.setObjectName(u"gunship_image_label")
        self.gunship_image_label.setMinimumSize(QSize(180, 137))
        self.gunship_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.suit_colors_layout.addWidget(self.gunship_image_label, 2, 2, 1, 2)

        self.power_suit_name_label = QLabel(self.suit_colors_foldable)
        self.power_suit_name_label.setObjectName(u"power_suit_name_label")
        self.power_suit_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.suit_colors_layout.addWidget(self.power_suit_name_label, 3, 0, 1, 1)

        self.varia_suit_name_label = QLabel(self.suit_colors_foldable)
        self.varia_suit_name_label.setObjectName(u"varia_suit_name_label")
        self.varia_suit_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.suit_colors_layout.addWidget(self.varia_suit_name_label, 3, 1, 1, 1)

        self.gravity_suit_name_label = QLabel(self.suit_colors_foldable)
        self.gravity_suit_name_label.setObjectName(u"gravity_suit_name_label")
        self.gravity_suit_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.suit_colors_layout.addWidget(self.gravity_suit_name_label, 3, 2, 1, 1)

        self.phazon_suit_name_label = QLabel(self.suit_colors_foldable)
        self.phazon_suit_name_label.setObjectName(u"phazon_suit_name_label")
        self.phazon_suit_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.suit_colors_layout.addWidget(self.phazon_suit_name_label, 3, 3, 1, 1)

        self.power_suit_rotation_slider = ScrollProtectedSlider(self.suit_colors_foldable)
        self.power_suit_rotation_slider.setObjectName(u"power_suit_rotation_slider")
        self.power_suit_rotation_slider.setMaximum(360)
        self.power_suit_rotation_slider.setSingleStep(5)
        self.power_suit_rotation_slider.setPageStep(30)
        self.power_suit_rotation_slider.setOrientation(Qt.Orientation.Horizontal)
        self.power_suit_rotation_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.power_suit_rotation_slider.setTickInterval(90)

        self.suit_colors_layout.addWidget(self.power_suit_rotation_slider, 4, 0, 1, 1)

        self.varia_suit_rotation_slider = ScrollProtectedSlider(self.suit_colors_foldable)
        self.varia_suit_rotation_slider.setObjectName(u"varia_suit_rotation_slider")
        self.varia_suit_rotation_slider.setMaximum(360)
        self.varia_suit_rotation_slider.setSingleStep(5)
        self.varia_suit_rotation_slider.setPageStep(30)
        self.varia_suit_rotation_slider.setOrientation(Qt.Orientation.Horizontal)
        self.varia_suit_rotation_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.varia_suit_rotation_slider.setTickInterval(90)

        self.suit_colors_layout.addWidget(self.varia_suit_rotation_slider, 4, 1, 1, 1)

        self.gravity_suit_rotation_slider = ScrollProtectedSlider(self.suit_colors_foldable)
        self.gravity_suit_rotation_slider.setObjectName(u"gravity_suit_rotation_slider")
        self.gravity_suit_rotation_slider.setMaximum(360)
        self.gravity_suit_rotation_slider.setSingleStep(5)
        self.gravity_suit_rotation_slider.setPageStep(30)
        self.gravity_suit_rotation_slider.setOrientation(Qt.Orientation.Horizontal)
        self.gravity_suit_rotation_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.gravity_suit_rotation_slider.setTickInterval(90)

        self.suit_colors_layout.addWidget(self.gravity_suit_rotation_slider, 4, 2, 1, 1)

        self.phazon_suit_rotation_slider = ScrollProtectedSlider(self.suit_colors_foldable)
        self.phazon_suit_rotation_slider.setObjectName(u"phazon_suit_rotation_slider")
        self.phazon_suit_rotation_slider.setMaximum(360)
        self.phazon_suit_rotation_slider.setSingleStep(5)
        self.phazon_suit_rotation_slider.setPageStep(30)
        self.phazon_suit_rotation_slider.setOrientation(Qt.Orientation.Horizontal)
        self.phazon_suit_rotation_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.phazon_suit_rotation_slider.setTickInterval(90)

        self.suit_colors_layout.addWidget(self.phazon_suit_rotation_slider, 4, 3, 1, 1)

        self.power_suit_image_label = QLabel(self.suit_colors_foldable)
        self.power_suit_image_label.setObjectName(u"power_suit_image_label")
        self.power_suit_image_label.setMinimumSize(QSize(130, 188))
        self.power_suit_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.suit_colors_layout.addWidget(self.power_suit_image_label, 5, 0, 1, 1)

        self.varia_suit_image_label = QLabel(self.suit_colors_foldable)
        self.varia_suit_image_label.setObjectName(u"varia_suit_image_label")
        self.varia_suit_image_label.setMinimumSize(QSize(130, 188))
        self.varia_suit_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.suit_colors_layout.addWidget(self.varia_suit_image_label, 5, 1, 1, 1)

        self.gravity_suit_image_label = QLabel(self.suit_colors_foldable)
        self.gravity_suit_image_label.setObjectName(u"gravity_suit_image_label")
        self.gravity_suit_image_label.setMinimumSize(QSize(130, 188))
        self.gravity_suit_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.suit_colors_layout.addWidget(self.gravity_suit_image_label, 5, 2, 1, 1)

        self.phazon_suit_image_label = QLabel(self.suit_colors_foldable)
        self.phazon_suit_image_label.setObjectName(u"phazon_suit_image_label")
        self.phazon_suit_image_label.setMinimumSize(QSize(130, 188))
        self.phazon_suit_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.suit_colors_layout.addWidget(self.phazon_suit_image_label, 5, 3, 1, 1)

        self.power_ball_image_label = QLabel(self.suit_colors_foldable)
        self.power_ball_image_label.setObjectName(u"power_ball_image_label")
        self.power_ball_image_label.setMinimumSize(QSize(130, 140))
        self.power_ball_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.suit_colors_layout.addWidget(self.power_ball_image_label, 6, 0, 1, 1)

        self.varia_ball_image_label = QLabel(self.suit_colors_foldable)
        self.varia_ball_image_label.setObjectName(u"varia_ball_image_label")
        self.varia_ball_image_label.setMinimumSize(QSize(130, 140))
        self.varia_ball_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.suit_colors_layout.addWidget(self.varia_ball_image_label, 6, 1, 1, 1)

        self.gravity_ball_image_label = QLabel(self.suit_colors_foldable)
        self.gravity_ball_image_label.setObjectName(u"gravity_ball_image_label")
        self.gravity_ball_image_label.setMinimumSize(QSize(130, 140))
        self.gravity_ball_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.suit_colors_layout.addWidget(self.gravity_ball_image_label, 6, 2, 1, 1)

        self.phazon_ball_image_label = QLabel(self.suit_colors_foldable)
        self.phazon_ball_image_label.setObjectName(u"phazon_ball_image_label")
        self.phazon_ball_image_label.setMinimumSize(QSize(130, 140))
        self.phazon_ball_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.suit_colors_layout.addWidget(self.phazon_ball_image_label, 6, 3, 1, 1)


        self.suit_colors_foldable_layout.addLayout(self.suit_colors_layout)


        self.verticalLayout.addWidget(self.suit_colors_foldable)

        self.options_foldable = Foldable(self.scroll_area_contents)
        self.options_foldable.setObjectName(u"options_foldable")
        self.options_foldable.setProperty(u"folded", True)
        self.options_foldable_layout = QVBoxLayout(self.options_foldable)
        self.options_foldable_layout.setSpacing(6)
        self.options_foldable_layout.setContentsMargins(11, 11, 11, 11)
        self.options_foldable_layout.setObjectName(u"options_foldable_layout")
        self.visor_box = QGroupBox(self.options_foldable)
        self.visor_box.setObjectName(u"visor_box")
        self.visor_layout = QGridLayout(self.visor_box)
        self.visor_layout.setSpacing(6)
        self.visor_layout.setContentsMargins(11, 11, 11, 11)
        self.visor_layout.setObjectName(u"visor_layout")
        self.hud_lag_check = QCheckBox(self.visor_box)
        self.hud_lag_check.setObjectName(u"hud_lag_check")

        self.visor_layout.addWidget(self.hud_lag_check, 3, 0, 1, 2)

        self.hud_alpha_label = QLabel(self.visor_box)
        self.hud_alpha_label.setObjectName(u"hud_alpha_label")

        self.visor_layout.addWidget(self.hud_alpha_label, 0, 0, 1, 1)

        self.helmet_alpha_slider = ScrollProtectedSlider(self.visor_box)
        self.helmet_alpha_slider.setObjectName(u"helmet_alpha_slider")
        self.helmet_alpha_slider.setOrientation(Qt.Orientation.Horizontal)
        self.helmet_alpha_slider.setTickPosition(QSlider.TickPosition.TicksBelow)

        self.visor_layout.addWidget(self.helmet_alpha_slider, 1, 1, 1, 1)

        self.hud_alpha_value_label = QLabel(self.visor_box)
        self.hud_alpha_value_label.setObjectName(u"hud_alpha_value_label")

        self.visor_layout.addWidget(self.hud_alpha_value_label, 0, 2, 1, 1)

        self.helmet_alpha_label = QLabel(self.visor_box)
        self.helmet_alpha_label.setObjectName(u"helmet_alpha_label")

        self.visor_layout.addWidget(self.helmet_alpha_label, 1, 0, 1, 1)

        self.helmet_alpha_value_label = QLabel(self.visor_box)
        self.helmet_alpha_value_label.setObjectName(u"helmet_alpha_value_label")

        self.visor_layout.addWidget(self.helmet_alpha_value_label, 1, 2, 1, 1)

        self.hud_alpha_slider = ScrollProtectedSlider(self.visor_box)
        self.hud_alpha_slider.setObjectName(u"hud_alpha_slider")
        self.hud_alpha_slider.setOrientation(Qt.Orientation.Horizontal)
        self.hud_alpha_slider.setTickPosition(QSlider.TickPosition.TicksBelow)

        self.visor_layout.addWidget(self.hud_alpha_slider, 0, 1, 1, 1)

        self.checkBox = QCheckBox(self.visor_box)
        self.checkBox.setObjectName(u"checkBox")
        self.checkBox.setEnabled(False)

        self.visor_layout.addWidget(self.checkBox, 4, 0, 1, 2)


        self.options_foldable_layout.addWidget(self.visor_box)

        self.controls_box = QGroupBox(self.options_foldable)
        self.controls_box.setObjectName(u"controls_box")
        self.controls_layout = QGridLayout(self.controls_box)
        self.controls_layout.setSpacing(6)
        self.controls_layout.setContentsMargins(11, 11, 11, 11)
        self.controls_layout.setObjectName(u"controls_layout")
        self.invert_y_axis_check = QCheckBox(self.controls_box)
        self.invert_y_axis_check.setObjectName(u"invert_y_axis_check")

        self.controls_layout.addWidget(self.invert_y_axis_check, 0, 0, 1, 1)

        self.rumble_check = QCheckBox(self.controls_box)
        self.rumble_check.setObjectName(u"rumble_check")

        self.controls_layout.addWidget(self.rumble_check, 1, 0, 1, 1)

        self.swap_beam_controls_check = QCheckBox(self.controls_box)
        self.swap_beam_controls_check.setObjectName(u"swap_beam_controls_check")

        self.controls_layout.addWidget(self.swap_beam_controls_check, 2, 0, 1, 1)


        self.options_foldable_layout.addWidget(self.controls_box)

        self.audio_box = QGroupBox(self.options_foldable)
        self.audio_box.setObjectName(u"audio_box")
        self.audio_layout = QGridLayout(self.audio_box)
        self.audio_layout.setSpacing(6)
        self.audio_layout.setContentsMargins(11, 11, 11, 11)
        self.audio_layout.setObjectName(u"audio_layout")
        self.sound_mode_label = QLabel(self.audio_box)
        self.sound_mode_label.setObjectName(u"sound_mode_label")
        self.sound_mode_label.setMaximumSize(QSize(16777215, 20))

        self.audio_layout.addWidget(self.sound_mode_label, 0, 0, 1, 1)

        self.sfx_volume_label = QLabel(self.audio_box)
        self.sfx_volume_label.setObjectName(u"sfx_volume_label")

        self.audio_layout.addWidget(self.sfx_volume_label, 1, 0, 1, 1)

        self.music_volume_label = QLabel(self.audio_box)
        self.music_volume_label.setObjectName(u"music_volume_label")

        self.audio_layout.addWidget(self.music_volume_label, 2, 0, 1, 1)

        self.sound_mode_combo = QComboBox(self.audio_box)
        self.sound_mode_combo.setObjectName(u"sound_mode_combo")

        self.audio_layout.addWidget(self.sound_mode_combo, 0, 1, 1, 1)

        self.sfx_volume_slider = ScrollProtectedSlider(self.audio_box)
        self.sfx_volume_slider.setObjectName(u"sfx_volume_slider")
        self.sfx_volume_slider.setOrientation(Qt.Orientation.Horizontal)
        self.sfx_volume_slider.setTickPosition(QSlider.TickPosition.TicksBelow)

        self.audio_layout.addWidget(self.sfx_volume_slider, 1, 1, 1, 1)

        self.music_volume_slider = ScrollProtectedSlider(self.audio_box)
        self.music_volume_slider.setObjectName(u"music_volume_slider")
        self.music_volume_slider.setOrientation(Qt.Orientation.Horizontal)
        self.music_volume_slider.setTickPosition(QSlider.TickPosition.TicksBelow)

        self.audio_layout.addWidget(self.music_volume_slider, 2, 1, 1, 1)

        self.sfx_volume_value_label = QLabel(self.audio_box)
        self.sfx_volume_value_label.setObjectName(u"sfx_volume_value_label")

        self.audio_layout.addWidget(self.sfx_volume_value_label, 1, 2, 1, 1)

        self.music_volume_value_label = QLabel(self.audio_box)
        self.music_volume_value_label.setObjectName(u"music_volume_value_label")

        self.audio_layout.addWidget(self.music_volume_value_label, 2, 2, 1, 1)


        self.options_foldable_layout.addWidget(self.audio_box)

        self.screen_box = QGroupBox(self.options_foldable)
        self.screen_box.setObjectName(u"screen_box")
        self.screen_layout = QGridLayout(self.screen_box)
        self.screen_layout.setSpacing(6)
        self.screen_layout.setContentsMargins(11, 11, 11, 11)
        self.screen_layout.setObjectName(u"screen_layout")
        self.screen_brightness_label = QLabel(self.screen_box)
        self.screen_brightness_label.setObjectName(u"screen_brightness_label")

        self.screen_layout.addWidget(self.screen_brightness_label, 0, 0, 1, 1)

        self.screen_x_offset_label = QLabel(self.screen_box)
        self.screen_x_offset_label.setObjectName(u"screen_x_offset_label")

        self.screen_layout.addWidget(self.screen_x_offset_label, 1, 0, 1, 1)

        self.screen_brightness_slider = ScrollProtectedSlider(self.screen_box)
        self.screen_brightness_slider.setObjectName(u"screen_brightness_slider")
        self.screen_brightness_slider.setOrientation(Qt.Orientation.Horizontal)
        self.screen_brightness_slider.setTickPosition(QSlider.TickPosition.TicksBelow)

        self.screen_layout.addWidget(self.screen_brightness_slider, 0, 1, 1, 1)

        self.screen_y_offset_slider = ScrollProtectedSlider(self.screen_box)
        self.screen_y_offset_slider.setObjectName(u"screen_y_offset_slider")
        self.screen_y_offset_slider.setOrientation(Qt.Orientation.Horizontal)
        self.screen_y_offset_slider.setTickPosition(QSlider.TickPosition.TicksBelow)

        self.screen_layout.addWidget(self.screen_y_offset_slider, 2, 1, 1, 1)

        self.screen_stretch_label = QLabel(self.screen_box)
        self.screen_stretch_label.setObjectName(u"screen_stretch_label")

        self.screen_layout.addWidget(self.screen_stretch_label, 3, 0, 1, 1)

        self.screen_x_offset_slider = ScrollProtectedSlider(self.screen_box)
        self.screen_x_offset_slider.setObjectName(u"screen_x_offset_slider")
        self.screen_x_offset_slider.setOrientation(Qt.Orientation.Horizontal)
        self.screen_x_offset_slider.setTickPosition(QSlider.TickPosition.TicksBelow)

        self.screen_layout.addWidget(self.screen_x_offset_slider, 1, 1, 1, 1)

        self.screen_stretch_slider = ScrollProtectedSlider(self.screen_box)
        self.screen_stretch_slider.setObjectName(u"screen_stretch_slider")
        self.screen_stretch_slider.setOrientation(Qt.Orientation.Horizontal)
        self.screen_stretch_slider.setTickPosition(QSlider.TickPosition.TicksBelow)

        self.screen_layout.addWidget(self.screen_stretch_slider, 3, 1, 1, 1)

        self.screen_y_offset_label = QLabel(self.screen_box)
        self.screen_y_offset_label.setObjectName(u"screen_y_offset_label")

        self.screen_layout.addWidget(self.screen_y_offset_label, 2, 0, 1, 1)

        self.screen_brightness_value_label = QLabel(self.screen_box)
        self.screen_brightness_value_label.setObjectName(u"screen_brightness_value_label")

        self.screen_layout.addWidget(self.screen_brightness_value_label, 0, 2, 1, 1)

        self.screen_x_offset_value_label = QLabel(self.screen_box)
        self.screen_x_offset_value_label.setObjectName(u"screen_x_offset_value_label")

        self.screen_layout.addWidget(self.screen_x_offset_value_label, 1, 2, 1, 1)

        self.screen_y_offset_value_label = QLabel(self.screen_box)
        self.screen_y_offset_value_label.setObjectName(u"screen_y_offset_value_label")

        self.screen_layout.addWidget(self.screen_y_offset_value_label, 2, 2, 1, 1)

        self.screen_stretch_value_label = QLabel(self.screen_box)
        self.screen_stretch_value_label.setObjectName(u"screen_stretch_value_label")

        self.screen_layout.addWidget(self.screen_stretch_value_label, 3, 2, 1, 1)


        self.options_foldable_layout.addWidget(self.screen_box)


        self.verticalLayout.addWidget(self.options_foldable)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.scrollArea.setWidget(self.scroll_area_contents)

        self.gridLayout.addWidget(self.scrollArea, 1, 0, 1, 3)


        self.retranslateUi(PrimeCosmeticPatchesDialog)

        self.accept_button.setDefault(True)


        QMetaObject.connectSlotsByName(PrimeCosmeticPatchesDialog)
    # setupUi

    def retranslateUi(self, PrimeCosmeticPatchesDialog):
        PrimeCosmeticPatchesDialog.setWindowTitle(QCoreApplication.translate("PrimeCosmeticPatchesDialog", u"Metroid Prime 1 - Cosmetic Options", None))
        self.reset_button.setText(QCoreApplication.translate("PrimeCosmeticPatchesDialog", u"Reset to Defaults", None))
        self.accept_button.setText(QCoreApplication.translate("PrimeCosmeticPatchesDialog", u"Accept", None))
        self.cancel_button.setText(QCoreApplication.translate("PrimeCosmeticPatchesDialog", u"Cancel", None))
        self.game_changes_box.setTitle(QCoreApplication.translate("PrimeCosmeticPatchesDialog", u"Game Changes", None))
        self.pickup_markers_check.setText(QCoreApplication.translate("PrimeCosmeticPatchesDialog", u"Add item icons on map", None))
        self.open_map_check.setText(QCoreApplication.translate("PrimeCosmeticPatchesDialog", u"Open map from start", None))
        self.custom_hud_color.setText(QCoreApplication.translate("PrimeCosmeticPatchesDialog", u"Use a custom HUD color", None))
        self.custom_hud_color_button.setText(QCoreApplication.translate("PrimeCosmeticPatchesDialog", u"Set Color...", None))
        self.suit_colors_foldable.setProperty(u"title", QCoreApplication.translate("PrimeCosmeticPatchesDialog", u"Suit Colors", None))
        self.force_fusion_check.setText(QCoreApplication.translate("PrimeCosmeticPatchesDialog", u"Fusion Suit", None))
        self.rainbow_phazon_ball_check.setText(QCoreApplication.translate("PrimeCosmeticPatchesDialog", u"Rainbow Ball (Phazon Suit)", None))
        self.gunship_name_label.setText(QCoreApplication.translate("PrimeCosmeticPatchesDialog", u"Gunship", None))
        self.gunship_header_separator_label.setText(QCoreApplication.translate("PrimeCosmeticPatchesDialog", u"|", None))
        self.match_gunship_to_power_suit_check.setText(QCoreApplication.translate("PrimeCosmeticPatchesDialog", u"Match Power Suit", None))
        self.gunship_image_label.setText("")
        self.power_suit_name_label.setText(QCoreApplication.translate("PrimeCosmeticPatchesDialog", u"Power", None))
        self.varia_suit_name_label.setText(QCoreApplication.translate("PrimeCosmeticPatchesDialog", u"Varia", None))
        self.gravity_suit_name_label.setText(QCoreApplication.translate("PrimeCosmeticPatchesDialog", u"Gravity", None))
        self.phazon_suit_name_label.setText(QCoreApplication.translate("PrimeCosmeticPatchesDialog", u"Phazon", None))
        self.power_suit_image_label.setText("")
        self.varia_suit_image_label.setText("")
        self.gravity_suit_image_label.setText("")
        self.phazon_suit_image_label.setText("")
        self.power_ball_image_label.setText("")
        self.varia_ball_image_label.setText("")
        self.gravity_ball_image_label.setText("")
        self.phazon_ball_image_label.setText("")
        self.options_foldable.setProperty(u"title", QCoreApplication.translate("PrimeCosmeticPatchesDialog", u"In-Game Options", None))
        self.visor_box.setTitle(QCoreApplication.translate("PrimeCosmeticPatchesDialog", u"Visor", None))
        self.hud_lag_check.setText(QCoreApplication.translate("PrimeCosmeticPatchesDialog", u"Hud Lag", None))
        self.hud_alpha_label.setText(QCoreApplication.translate("PrimeCosmeticPatchesDialog", u"Visor Opacity", None))
        self.hud_alpha_value_label.setText(QCoreApplication.translate("PrimeCosmeticPatchesDialog", u"TextLabel", None))
        self.helmet_alpha_label.setText(QCoreApplication.translate("PrimeCosmeticPatchesDialog", u"Helmet Opacity", None))
        self.helmet_alpha_value_label.setText(QCoreApplication.translate("PrimeCosmeticPatchesDialog", u"TextLabel", None))
#if QT_CONFIG(tooltip)
        self.checkBox.setToolTip(QCoreApplication.translate("PrimeCosmeticPatchesDialog", u"<html><head/><body><p>The in-game Hint System has been removed. The option for it remains, but does nothing.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.checkBox.setText(QCoreApplication.translate("PrimeCosmeticPatchesDialog", u"Hint System", None))
        self.controls_box.setTitle(QCoreApplication.translate("PrimeCosmeticPatchesDialog", u"Controls", None))
        self.invert_y_axis_check.setText(QCoreApplication.translate("PrimeCosmeticPatchesDialog", u"Invert Y Axis", None))
        self.rumble_check.setText(QCoreApplication.translate("PrimeCosmeticPatchesDialog", u"Rumble", None))
        self.swap_beam_controls_check.setText(QCoreApplication.translate("PrimeCosmeticPatchesDialog", u"Swap Beam Controls", None))
        self.audio_box.setTitle(QCoreApplication.translate("PrimeCosmeticPatchesDialog", u"Audio", None))
        self.sound_mode_label.setText(QCoreApplication.translate("PrimeCosmeticPatchesDialog", u"Sound Mode", None))
        self.sfx_volume_label.setText(QCoreApplication.translate("PrimeCosmeticPatchesDialog", u"Sound Volume", None))
        self.music_volume_label.setText(QCoreApplication.translate("PrimeCosmeticPatchesDialog", u"Music Volume", None))
        self.sfx_volume_value_label.setText(QCoreApplication.translate("PrimeCosmeticPatchesDialog", u"TextLabel", None))
        self.music_volume_value_label.setText(QCoreApplication.translate("PrimeCosmeticPatchesDialog", u"TextLabel", None))
        self.screen_box.setTitle(QCoreApplication.translate("PrimeCosmeticPatchesDialog", u"Screen", None))
        self.screen_brightness_label.setText(QCoreApplication.translate("PrimeCosmeticPatchesDialog", u"Screen Brightness", None))
        self.screen_x_offset_label.setText(QCoreApplication.translate("PrimeCosmeticPatchesDialog", u"Screen X Offset", None))
        self.screen_stretch_label.setText(QCoreApplication.translate("PrimeCosmeticPatchesDialog", u"Screen Stretch", None))
        self.screen_y_offset_label.setText(QCoreApplication.translate("PrimeCosmeticPatchesDialog", u"Screen Y Offset", None))
        self.screen_brightness_value_label.setText(QCoreApplication.translate("PrimeCosmeticPatchesDialog", u"TextLabel", None))
        self.screen_x_offset_value_label.setText(QCoreApplication.translate("PrimeCosmeticPatchesDialog", u"TextLabel", None))
        self.screen_y_offset_value_label.setText(QCoreApplication.translate("PrimeCosmeticPatchesDialog", u"TextLabel", None))
        self.screen_stretch_value_label.setText(QCoreApplication.translate("PrimeCosmeticPatchesDialog", u"TextLabel", None))
    # retranslateUi

