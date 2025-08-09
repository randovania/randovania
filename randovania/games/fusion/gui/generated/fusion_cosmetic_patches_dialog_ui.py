# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'fusion_cosmetic_patches_dialog.ui'
##
## Created by: Qt User Interface Compiler version 6.9.1
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
    QGridLayout, QGroupBox, QHBoxLayout, QLabel,
    QPushButton, QRadioButton, QScrollArea, QSizePolicy,
    QSpacerItem, QSpinBox, QVBoxLayout, QWidget)

class Ui_FusionCosmeticPatchesDialog(object):
    def setupUi(self, FusionCosmeticPatchesDialog):
        if not FusionCosmeticPatchesDialog.objectName():
            FusionCosmeticPatchesDialog.setObjectName(u"FusionCosmeticPatchesDialog")
        FusionCosmeticPatchesDialog.resize(700, 585)
        self.gridLayout = QGridLayout(FusionCosmeticPatchesDialog)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setContentsMargins(11, 11, 11, 11)
        self.gridLayout.setObjectName(u"gridLayout")
        self.reset_button = QPushButton(FusionCosmeticPatchesDialog)
        self.reset_button.setObjectName(u"reset_button")

        self.gridLayout.addWidget(self.reset_button, 3, 2, 1, 1)

        self.cancel_button = QPushButton(FusionCosmeticPatchesDialog)
        self.cancel_button.setObjectName(u"cancel_button")

        self.gridLayout.addWidget(self.cancel_button, 3, 1, 1, 1)

        self.accept_button = QPushButton(FusionCosmeticPatchesDialog)
        self.accept_button.setObjectName(u"accept_button")

        self.gridLayout.addWidget(self.accept_button, 3, 0, 1, 1)

        self.scrollArea = QScrollArea(FusionCosmeticPatchesDialog)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.scroll_area_contents = QWidget()
        self.scroll_area_contents.setObjectName(u"scroll_area_contents")
        self.scroll_area_contents.setGeometry(QRect(0, -8, 663, 586))
        self.verticalLayout = QVBoxLayout(self.scroll_area_contents)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.gameplay_box = QGroupBox(self.scroll_area_contents)
        self.gameplay_box.setObjectName(u"gameplay_box")
        self.verticalLayout_2 = QVBoxLayout(self.gameplay_box)
        self.verticalLayout_2.setSpacing(6)
        self.verticalLayout_2.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(9, 9, 9, 9)
        self.map_check = QCheckBox(self.gameplay_box)
        self.map_check.setObjectName(u"map_check")

        self.verticalLayout_2.addWidget(self.map_check)

        self.map_label = QLabel(self.gameplay_box)
        self.map_label.setObjectName(u"map_label")

        self.verticalLayout_2.addWidget(self.map_label)

        self.reveal_blocks_check = QCheckBox(self.gameplay_box)
        self.reveal_blocks_check.setObjectName(u"reveal_blocks_check")

        self.verticalLayout_2.addWidget(self.reveal_blocks_check)

        self.reveal_blocks_label = QLabel(self.gameplay_box)
        self.reveal_blocks_label.setObjectName(u"reveal_blocks_label")

        self.verticalLayout_2.addWidget(self.reveal_blocks_label)


        self.verticalLayout.addWidget(self.gameplay_box)

        self.palette_box = QGroupBox(self.scroll_area_contents)
        self.palette_box.setObjectName(u"palette_box")
        self.palette_layout = QVBoxLayout(self.palette_box)
        self.palette_layout.setSpacing(6)
        self.palette_layout.setContentsMargins(11, 11, 11, 11)
        self.palette_layout.setObjectName(u"palette_layout")
        self.suit_color_layout = QHBoxLayout()
        self.suit_color_layout.setSpacing(6)
        self.suit_color_layout.setObjectName(u"suit_color_layout")
        self.suit_palette_label = QLabel(self.palette_box)
        self.suit_palette_label.setObjectName(u"suit_palette_label")

        self.suit_color_layout.addWidget(self.suit_palette_label)

        self.suit_rando_shift_check = QCheckBox(self.palette_box)
        self.suit_rando_shift_check.setObjectName(u"suit_rando_shift_check")
        self.suit_rando_shift_check.setEnabled(True)

        self.suit_color_layout.addWidget(self.suit_rando_shift_check)

        self.suit_override_shift_check = QCheckBox(self.palette_box)
        self.suit_override_shift_check.setObjectName(u"suit_override_shift_check")
        self.suit_override_shift_check.setEnabled(False)
        self.suit_override_shift_check.setBaseSize(QSize(0, 0))
        self.suit_override_shift_check.setIconSize(QSize(16, 16))

        self.suit_color_layout.addWidget(self.suit_override_shift_check, 0, Qt.AlignmentFlag.AlignLeft)

        self.suit_override_shift_spin_min = QSpinBox(self.palette_box)
        self.suit_override_shift_spin_min.setObjectName(u"suit_override_shift_spin_min")
        self.suit_override_shift_spin_min.setEnabled(False)
        self.suit_override_shift_spin_min.setMaximumSize(QSize(50, 16777215))
        self.suit_override_shift_spin_min.setMaximum(360)
        self.suit_override_shift_spin_min.setSingleStep(5)

        self.suit_color_layout.addWidget(self.suit_override_shift_spin_min)

        self.suit_override_shift_spin_max = QSpinBox(self.palette_box)
        self.suit_override_shift_spin_max.setObjectName(u"suit_override_shift_spin_max")
        self.suit_override_shift_spin_max.setEnabled(False)
        self.suit_override_shift_spin_max.setMinimumSize(QSize(0, 0))
        self.suit_override_shift_spin_max.setMaximumSize(QSize(50, 16777215))
        self.suit_override_shift_spin_max.setMaximum(360)
        self.suit_override_shift_spin_max.setSingleStep(5)

        self.suit_color_layout.addWidget(self.suit_override_shift_spin_max)


        self.palette_layout.addLayout(self.suit_color_layout)

        self.beam_color_layout = QHBoxLayout()
        self.beam_color_layout.setSpacing(6)
        self.beam_color_layout.setObjectName(u"beam_color_layout")
        self.beam_palette_label = QLabel(self.palette_box)
        self.beam_palette_label.setObjectName(u"beam_palette_label")

        self.beam_color_layout.addWidget(self.beam_palette_label)

        self.beam_rando_shift_check = QCheckBox(self.palette_box)
        self.beam_rando_shift_check.setObjectName(u"beam_rando_shift_check")
        self.beam_rando_shift_check.setEnabled(True)

        self.beam_color_layout.addWidget(self.beam_rando_shift_check)

        self.beam_override_shift_check = QCheckBox(self.palette_box)
        self.beam_override_shift_check.setObjectName(u"beam_override_shift_check")
        self.beam_override_shift_check.setEnabled(False)

        self.beam_color_layout.addWidget(self.beam_override_shift_check, 0, Qt.AlignmentFlag.AlignLeft)

        self.beam_override_shift_spin_min = QSpinBox(self.palette_box)
        self.beam_override_shift_spin_min.setObjectName(u"beam_override_shift_spin_min")
        self.beam_override_shift_spin_min.setEnabled(False)
        self.beam_override_shift_spin_min.setMaximumSize(QSize(50, 16777215))
        self.beam_override_shift_spin_min.setMaximum(360)
        self.beam_override_shift_spin_min.setSingleStep(5)

        self.beam_color_layout.addWidget(self.beam_override_shift_spin_min)

        self.beam_override_shift_spin_max = QSpinBox(self.palette_box)
        self.beam_override_shift_spin_max.setObjectName(u"beam_override_shift_spin_max")
        self.beam_override_shift_spin_max.setEnabled(False)
        self.beam_override_shift_spin_max.setMaximumSize(QSize(50, 16777215))
        self.beam_override_shift_spin_max.setMaximum(360)
        self.beam_override_shift_spin_max.setSingleStep(5)

        self.beam_color_layout.addWidget(self.beam_override_shift_spin_max)


        self.palette_layout.addLayout(self.beam_color_layout)

        self.enemy_color_layout = QHBoxLayout()
        self.enemy_color_layout.setSpacing(6)
        self.enemy_color_layout.setObjectName(u"enemy_color_layout")
        self.enemy_palette_label = QLabel(self.palette_box)
        self.enemy_palette_label.setObjectName(u"enemy_palette_label")

        self.enemy_color_layout.addWidget(self.enemy_palette_label)

        self.enemy_rando_shift_check = QCheckBox(self.palette_box)
        self.enemy_rando_shift_check.setObjectName(u"enemy_rando_shift_check")
        self.enemy_rando_shift_check.setEnabled(True)

        self.enemy_color_layout.addWidget(self.enemy_rando_shift_check)

        self.enemy_override_shift_check = QCheckBox(self.palette_box)
        self.enemy_override_shift_check.setObjectName(u"enemy_override_shift_check")
        self.enemy_override_shift_check.setEnabled(False)

        self.enemy_color_layout.addWidget(self.enemy_override_shift_check, 0, Qt.AlignmentFlag.AlignLeft)

        self.enemy_override_shift_spin_min = QSpinBox(self.palette_box)
        self.enemy_override_shift_spin_min.setObjectName(u"enemy_override_shift_spin_min")
        self.enemy_override_shift_spin_min.setEnabled(False)
        self.enemy_override_shift_spin_min.setMaximumSize(QSize(50, 16777215))
        self.enemy_override_shift_spin_min.setMaximum(360)
        self.enemy_override_shift_spin_min.setSingleStep(5)

        self.enemy_color_layout.addWidget(self.enemy_override_shift_spin_min)

        self.enemy_override_shift_spin_max = QSpinBox(self.palette_box)
        self.enemy_override_shift_spin_max.setObjectName(u"enemy_override_shift_spin_max")
        self.enemy_override_shift_spin_max.setEnabled(False)
        self.enemy_override_shift_spin_max.setMaximumSize(QSize(50, 16777215))
        self.enemy_override_shift_spin_max.setMaximum(360)
        self.enemy_override_shift_spin_max.setSingleStep(5)

        self.enemy_color_layout.addWidget(self.enemy_override_shift_spin_max)


        self.palette_layout.addLayout(self.enemy_color_layout)

        self.tileset_color_layout = QHBoxLayout()
        self.tileset_color_layout.setSpacing(6)
        self.tileset_color_layout.setObjectName(u"tileset_color_layout")
        self.tileset_palette_label = QLabel(self.palette_box)
        self.tileset_palette_label.setObjectName(u"tileset_palette_label")

        self.tileset_color_layout.addWidget(self.tileset_palette_label)

        self.tileset_rando_shift_check = QCheckBox(self.palette_box)
        self.tileset_rando_shift_check.setObjectName(u"tileset_rando_shift_check")
        self.tileset_rando_shift_check.setEnabled(True)

        self.tileset_color_layout.addWidget(self.tileset_rando_shift_check)

        self.tileset_override_shift_check = QCheckBox(self.palette_box)
        self.tileset_override_shift_check.setObjectName(u"tileset_override_shift_check")
        self.tileset_override_shift_check.setEnabled(False)

        self.tileset_color_layout.addWidget(self.tileset_override_shift_check, 0, Qt.AlignmentFlag.AlignLeft)

        self.tileset_override_shift_spin_min = QSpinBox(self.palette_box)
        self.tileset_override_shift_spin_min.setObjectName(u"tileset_override_shift_spin_min")
        self.tileset_override_shift_spin_min.setEnabled(False)
        self.tileset_override_shift_spin_min.setMaximumSize(QSize(50, 16777215))
        self.tileset_override_shift_spin_min.setMinimum(0)
        self.tileset_override_shift_spin_min.setMaximum(360)
        self.tileset_override_shift_spin_min.setSingleStep(5)
        self.tileset_override_shift_spin_min.setValue(0)

        self.tileset_color_layout.addWidget(self.tileset_override_shift_spin_min)

        self.tileset_override_shift_spin_max = QSpinBox(self.palette_box)
        self.tileset_override_shift_spin_max.setObjectName(u"tileset_override_shift_spin_max")
        self.tileset_override_shift_spin_max.setEnabled(False)
        self.tileset_override_shift_spin_max.setMaximumSize(QSize(50, 16777215))
        self.tileset_override_shift_spin_max.setMaximum(360)
        self.tileset_override_shift_spin_max.setSingleStep(5)

        self.tileset_color_layout.addWidget(self.tileset_override_shift_spin_max)


        self.palette_layout.addLayout(self.tileset_color_layout)

        self.color_space_layout = QGridLayout()
        self.color_space_layout.setSpacing(6)
        self.color_space_layout.setObjectName(u"color_space_layout")
        self.color_space_label = QLabel(self.palette_box)
        self.color_space_label.setObjectName(u"color_space_label")
        self.color_space_label.setMaximumSize(QSize(16777215, 20))

        self.color_space_layout.addWidget(self.color_space_label, 0, 0, 1, 1, Qt.AlignmentFlag.AlignLeft)

        self.symmetric_check = QCheckBox(self.palette_box)
        self.symmetric_check.setObjectName(u"symmetric_check")
        self.symmetric_check.setChecked(False)

        self.color_space_layout.addWidget(self.symmetric_check, 0, 2, 1, 1, Qt.AlignmentFlag.AlignHCenter)

        self.color_space_combo = QComboBox(self.palette_box)
        self.color_space_combo.setObjectName(u"color_space_combo")
        self.color_space_combo.setMinimumSize(QSize(0, 0))

        self.color_space_layout.addWidget(self.color_space_combo, 0, 1, 1, 1)


        self.palette_layout.addLayout(self.color_space_layout)


        self.verticalLayout.addWidget(self.palette_box)

        self.audio_box = QGroupBox(self.scroll_area_contents)
        self.audio_box.setObjectName(u"audio_box")
        self.audio_layout = QVBoxLayout(self.audio_box)
        self.audio_layout.setSpacing(6)
        self.audio_layout.setContentsMargins(11, 11, 11, 11)
        self.audio_layout.setObjectName(u"audio_layout")
        self.default_audio_label = QLabel(self.audio_box)
        self.default_audio_label.setObjectName(u"default_audio_label")

        self.audio_layout.addWidget(self.default_audio_label)

        self.stereo_layout = QHBoxLayout()
        self.stereo_layout.setSpacing(6)
        self.stereo_layout.setObjectName(u"stereo_layout")
        self.mono_option = QRadioButton(self.audio_box)
        self.mono_option.setObjectName(u"mono_option")
        self.mono_option.setChecked(False)

        self.stereo_layout.addWidget(self.mono_option)

        self.stereo_option = QRadioButton(self.audio_box)
        self.stereo_option.setObjectName(u"stereo_option")
        self.stereo_option.setChecked(True)

        self.stereo_layout.addWidget(self.stereo_option)


        self.audio_layout.addLayout(self.stereo_layout)

        self.audio_volume_label = QLabel(self.audio_box)
        self.audio_volume_label.setObjectName(u"audio_volume_label")

        self.audio_layout.addWidget(self.audio_volume_label)

        self.volume_layout = QHBoxLayout()
        self.volume_layout.setSpacing(6)
        self.volume_layout.setObjectName(u"volume_layout")
        self.disable_music_check = QCheckBox(self.audio_box)
        self.disable_music_check.setObjectName(u"disable_music_check")

        self.volume_layout.addWidget(self.disable_music_check)


        self.audio_layout.addLayout(self.volume_layout)

        self.music_layout = QHBoxLayout()
        self.music_layout.setSpacing(6)
        self.music_layout.setObjectName(u"music_layout")
        self.disable_sfx_check = QCheckBox(self.audio_box)
        self.disable_sfx_check.setObjectName(u"disable_sfx_check")

        self.music_layout.addWidget(self.disable_sfx_check)


        self.audio_layout.addLayout(self.music_layout)


        self.verticalLayout.addWidget(self.audio_box)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.scrollArea.setWidget(self.scroll_area_contents)

        self.gridLayout.addWidget(self.scrollArea, 1, 0, 1, 3)


        self.retranslateUi(FusionCosmeticPatchesDialog)

        self.accept_button.setDefault(True)


        QMetaObject.connectSlotsByName(FusionCosmeticPatchesDialog)
    # setupUi

    def retranslateUi(self, FusionCosmeticPatchesDialog):
        FusionCosmeticPatchesDialog.setWindowTitle(QCoreApplication.translate("FusionCosmeticPatchesDialog", u"Metroid Fusion - Cosmetic Options", None))
        self.reset_button.setText(QCoreApplication.translate("FusionCosmeticPatchesDialog", u"Reset to Defaults", None))
        self.cancel_button.setText(QCoreApplication.translate("FusionCosmeticPatchesDialog", u"Cancel", None))
        self.accept_button.setText(QCoreApplication.translate("FusionCosmeticPatchesDialog", u"Accept", None))
        self.gameplay_box.setTitle(QCoreApplication.translate("FusionCosmeticPatchesDialog", u"General Gameplay", None))
        self.map_check.setText(QCoreApplication.translate("FusionCosmeticPatchesDialog", u"Show unexplored map from start", None))
        self.map_label.setText(QCoreApplication.translate("FusionCosmeticPatchesDialog", u"This setting reveals the entire map including item dots", None))
        self.reveal_blocks_check.setText(QCoreApplication.translate("FusionCosmeticPatchesDialog", u"Reveal hidden blocks", None))
        self.reveal_blocks_label.setText(QCoreApplication.translate("FusionCosmeticPatchesDialog", u"Blocks that normally need bombs to be revealed are now always visible.", None))
        self.palette_box.setTitle(QCoreApplication.translate("FusionCosmeticPatchesDialog", u"Color Rotation", None))
        self.suit_palette_label.setText(QCoreApplication.translate("FusionCosmeticPatchesDialog", u"Suit Palette", None))
        self.suit_rando_shift_check.setText(QCoreApplication.translate("FusionCosmeticPatchesDialog", u"Randomize Hue Shift", None))
        self.suit_override_shift_check.setText(QCoreApplication.translate("FusionCosmeticPatchesDialog", u"Override Hue Shift (min,max)", None))
        self.beam_palette_label.setText(QCoreApplication.translate("FusionCosmeticPatchesDialog", u"Beam Palette", None))
        self.beam_rando_shift_check.setText(QCoreApplication.translate("FusionCosmeticPatchesDialog", u"Randomize Hue Shift", None))
        self.beam_override_shift_check.setText(QCoreApplication.translate("FusionCosmeticPatchesDialog", u"Override Hue Shift (min,max)", None))
        self.enemy_palette_label.setText(QCoreApplication.translate("FusionCosmeticPatchesDialog", u"Enemy Palette", None))
        self.enemy_rando_shift_check.setText(QCoreApplication.translate("FusionCosmeticPatchesDialog", u"Randomize Hue Shift", None))
        self.enemy_override_shift_check.setText(QCoreApplication.translate("FusionCosmeticPatchesDialog", u"Override Hue Shift (min,max)", None))
        self.tileset_palette_label.setText(QCoreApplication.translate("FusionCosmeticPatchesDialog", u"Tileset Palette", None))
        self.tileset_rando_shift_check.setText(QCoreApplication.translate("FusionCosmeticPatchesDialog", u"Randomize Hue Shift", None))
        self.tileset_override_shift_check.setText(QCoreApplication.translate("FusionCosmeticPatchesDialog", u"Override Hue Shift (min,max)", None))
        self.color_space_label.setText(QCoreApplication.translate("FusionCosmeticPatchesDialog", u"Color Space", None))
        self.symmetric_check.setText(QCoreApplication.translate("FusionCosmeticPatchesDialog", u"Enable Symmetric", None))
        self.audio_box.setTitle(QCoreApplication.translate("FusionCosmeticPatchesDialog", u"Audio Options", None))
        self.default_audio_label.setText(QCoreApplication.translate("FusionCosmeticPatchesDialog", u"Default Audio Settings:", None))
        self.mono_option.setText(QCoreApplication.translate("FusionCosmeticPatchesDialog", u"Mono", None))
        self.stereo_option.setText(QCoreApplication.translate("FusionCosmeticPatchesDialog", u"Stereo", None))
        self.audio_volume_label.setText(QCoreApplication.translate("FusionCosmeticPatchesDialog", u"Audio Volume Settings:", None))
        self.disable_music_check.setText(QCoreApplication.translate("FusionCosmeticPatchesDialog", u"Mute Music", None))
        self.disable_sfx_check.setText(QCoreApplication.translate("FusionCosmeticPatchesDialog", u"Mute Sound Effects", None))
    # retranslateUi

