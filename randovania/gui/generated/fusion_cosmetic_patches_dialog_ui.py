# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'fusion_cosmetic_patches_dialog.ui'
##
## Created by: Qt User Interface Compiler version 6.6.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import *  # type: ignore
from PySide6.QtGui import *  # type: ignore
from PySide6.QtWidgets import *  # type: ignore

class Ui_FusionCosmeticPatchesDialog(object):
    def setupUi(self, FusionCosmeticPatchesDialog):
        if not FusionCosmeticPatchesDialog.objectName():
            FusionCosmeticPatchesDialog.setObjectName(u"FusionCosmeticPatchesDialog")
        FusionCosmeticPatchesDialog.resize(396, 246)
        self.gridLayout = QGridLayout(FusionCosmeticPatchesDialog)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setContentsMargins(11, 11, 11, 11)
        self.gridLayout.setObjectName(u"gridLayout")
        self.reset_button = QPushButton(FusionCosmeticPatchesDialog)
        self.reset_button.setObjectName(u"reset_button")

        self.gridLayout.addWidget(self.reset_button, 2, 2, 1, 1)

        self.accept_button = QPushButton(FusionCosmeticPatchesDialog)
        self.accept_button.setObjectName(u"accept_button")

        self.gridLayout.addWidget(self.accept_button, 2, 0, 1, 1)

        self.cancel_button = QPushButton(FusionCosmeticPatchesDialog)
        self.cancel_button.setObjectName(u"cancel_button")

        self.gridLayout.addWidget(self.cancel_button, 2, 1, 1, 1)

        self.scrollArea = QScrollArea(FusionCosmeticPatchesDialog)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.scroll_area_contents = QWidget()
        self.scroll_area_contents.setObjectName(u"scroll_area_contents")
        self.scroll_area_contents.setGeometry(QRect(0, -200, 362, 406))
        self.verticalLayout = QVBoxLayout(self.scroll_area_contents)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.palette_box = QGroupBox(self.scroll_area_contents)
        self.palette_box.setObjectName(u"palette_box")
        self.palette_layout = QVBoxLayout(self.palette_box)
        self.palette_layout.setSpacing(6)
        self.palette_layout.setContentsMargins(11, 11, 11, 11)
        self.palette_layout.setObjectName(u"palette_layout")
        self.suit_color_layout = QHBoxLayout()
        self.suit_color_layout.setSpacing(6)
        self.suit_color_layout.setObjectName(u"suit_color_layout")
        self.suit_palette_check = QCheckBox(self.palette_box)
        self.suit_palette_check.setObjectName(u"suit_palette_check")

        self.suit_color_layout.addWidget(self.suit_palette_check)


        self.palette_layout.addLayout(self.suit_color_layout)

        self.beam_color_layout = QHBoxLayout()
        self.beam_color_layout.setSpacing(6)
        self.beam_color_layout.setObjectName(u"beam_color_layout")
        self.beam_palette_check = QCheckBox(self.palette_box)
        self.beam_palette_check.setObjectName(u"beam_palette_check")

        self.beam_color_layout.addWidget(self.beam_palette_check)


        self.palette_layout.addLayout(self.beam_color_layout)

        self.enemy_color_layout = QHBoxLayout()
        self.enemy_color_layout.setSpacing(6)
        self.enemy_color_layout.setObjectName(u"enemy_color_layout")
        self.enemy_palette_check = QCheckBox(self.palette_box)
        self.enemy_palette_check.setObjectName(u"enemy_palette_check")

        self.enemy_color_layout.addWidget(self.enemy_palette_check)


        self.palette_layout.addLayout(self.enemy_color_layout)

        self.tileset_color_layout = QHBoxLayout()
        self.tileset_color_layout.setSpacing(6)
        self.tileset_color_layout.setObjectName(u"tileset_color_layout")
        self.tileset_palette_check = QCheckBox(self.palette_box)
        self.tileset_palette_check.setObjectName(u"tileset_palette_check")

        self.tileset_color_layout.addWidget(self.tileset_palette_check)


        self.palette_layout.addLayout(self.tileset_color_layout)

        self.color_space_layout = QGridLayout()
        self.color_space_layout.setSpacing(6)
        self.color_space_layout.setObjectName(u"color_space_layout")
        self.color_space_combo = QComboBox(self.palette_box)
        self.color_space_combo.setObjectName(u"color_space_combo")

        self.color_space_layout.addWidget(self.color_space_combo, 0, 1, 1, 1)

        self.color_space_label = QLabel(self.palette_box)
        self.color_space_label.setObjectName(u"color_space_label")
        self.color_space_label.setMaximumSize(QSize(16777215, 20))

        self.color_space_layout.addWidget(self.color_space_label, 0, 0, 1, 1)


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

        self.verticalSpacer = QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        self.audio_layout.addItem(self.verticalSpacer)

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

        self.verticalSpacer1 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer1)

        self.scrollArea.setWidget(self.scroll_area_contents)

        self.gridLayout.addWidget(self.scrollArea, 1, 0, 1, 3)


        self.retranslateUi(FusionCosmeticPatchesDialog)

        QMetaObject.connectSlotsByName(FusionCosmeticPatchesDialog)
    # setupUi

    def retranslateUi(self, FusionCosmeticPatchesDialog):
        FusionCosmeticPatchesDialog.setWindowTitle(QCoreApplication.translate("FusionCosmeticPatchesDialog", u"Metroid Fusion - Cosmetic Options", None))
        self.reset_button.setText(QCoreApplication.translate("FusionCosmeticPatchesDialog", u"Reset to Defaults", None))
        self.accept_button.setText(QCoreApplication.translate("FusionCosmeticPatchesDialog", u"Accept", None))
        self.cancel_button.setText(QCoreApplication.translate("FusionCosmeticPatchesDialog", u"Cancel", None))
        self.palette_box.setTitle(QCoreApplication.translate("FusionCosmeticPatchesDialog", u"Palette Shuffle", None))
        self.suit_palette_check.setText(QCoreApplication.translate("FusionCosmeticPatchesDialog", u"Randomize Suit Pallete", None))
        self.beam_palette_check.setText(QCoreApplication.translate("FusionCosmeticPatchesDialog", u"Randomize Beam Pallete", None))
        self.enemy_palette_check.setText(QCoreApplication.translate("FusionCosmeticPatchesDialog", u"Randomize Enemy Pallete", None))
        self.tileset_palette_check.setText(QCoreApplication.translate("FusionCosmeticPatchesDialog", u"Randomize Tileset Pallete", None))
        self.color_space_label.setText(QCoreApplication.translate("FusionCosmeticPatchesDialog", u"Color Space", None))
        self.audio_box.setTitle(QCoreApplication.translate("FusionCosmeticPatchesDialog", u"Audio Options", None))
        self.default_audio_label.setText(QCoreApplication.translate("FusionCosmeticPatchesDialog", u"Default Audio Settings:", None))
        self.mono_option.setText(QCoreApplication.translate("FusionCosmeticPatchesDialog", u"Mono", None))
        self.stereo_option.setText(QCoreApplication.translate("FusionCosmeticPatchesDialog", u"Stereo", None))
        self.audio_volume_label.setText(QCoreApplication.translate("FusionCosmeticPatchesDialog", u"Audio Volume Settings:", None))
        self.disable_music_check.setText(QCoreApplication.translate("FusionCosmeticPatchesDialog", u"Mute Music", None))
        self.disable_sfx_check.setText(QCoreApplication.translate("FusionCosmeticPatchesDialog", u"Mute Sound Effects", None))
    # retranslateUi

