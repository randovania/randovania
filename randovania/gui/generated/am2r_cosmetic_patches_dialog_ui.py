# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'am2r_cosmetic_patches_dialog.ui'
##
## Created by: Qt User Interface Compiler version 6.6.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import *  # type: ignore
from PySide6.QtGui import *  # type: ignore
from PySide6.QtWidgets import *  # type: ignore

class Ui_AM2RCosmeticPatchesDialog(object):
    def setupUi(self, AM2RCosmeticPatchesDialog):
        if not AM2RCosmeticPatchesDialog.objectName():
            AM2RCosmeticPatchesDialog.setObjectName(u"AM2RCosmeticPatchesDialog")
        AM2RCosmeticPatchesDialog.resize(460, 389)
        self.gridLayout = QGridLayout(AM2RCosmeticPatchesDialog)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setContentsMargins(11, 11, 11, 11)
        self.gridLayout.setObjectName(u"gridLayout")
        self.accept_button = QPushButton(AM2RCosmeticPatchesDialog)
        self.accept_button.setObjectName(u"accept_button")

        self.gridLayout.addWidget(self.accept_button, 2, 0, 1, 1)

        self.reset_button = QPushButton(AM2RCosmeticPatchesDialog)
        self.reset_button.setObjectName(u"reset_button")

        self.gridLayout.addWidget(self.reset_button, 2, 2, 1, 1)

        self.cancel_button = QPushButton(AM2RCosmeticPatchesDialog)
        self.cancel_button.setObjectName(u"cancel_button")

        self.gridLayout.addWidget(self.cancel_button, 2, 1, 1, 1)

        self.scrollArea = QScrollArea(AM2RCosmeticPatchesDialog)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.scroll_area_contents = QWidget()
        self.scroll_area_contents.setObjectName(u"scroll_area_contents")
        self.scroll_area_contents.setGeometry(QRect(0, 0, 423, 694))
        self.verticalLayout = QVBoxLayout(self.scroll_area_contents)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label = QLabel(self.scroll_area_contents)
        self.label.setObjectName(u"label")
        self.label.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.label)

        self.show_unexplored_map_check = QCheckBox(self.scroll_area_contents)
        self.show_unexplored_map_check.setObjectName(u"show_unexplored_map_check")

        self.verticalLayout.addWidget(self.show_unexplored_map_check)

        self.show_unexplored_map_label = QLabel(self.scroll_area_contents)
        self.show_unexplored_map_label.setObjectName(u"show_unexplored_map_label")
        self.show_unexplored_map_label.setWordWrap(True)

        self.verticalLayout.addWidget(self.show_unexplored_map_label)

        self.unveiled_blocks_check = QCheckBox(self.scroll_area_contents)
        self.unveiled_blocks_check.setObjectName(u"unveiled_blocks_check")

        self.verticalLayout.addWidget(self.unveiled_blocks_check)

        self.unveiled_blocks_label = QLabel(self.scroll_area_contents)
        self.unveiled_blocks_label.setObjectName(u"unveiled_blocks_label")
        self.unveiled_blocks_label.setWordWrap(True)

        self.verticalLayout.addWidget(self.unveiled_blocks_label)

        self.room_name_layout = QHBoxLayout()
        self.room_name_layout.setSpacing(6)
        self.room_name_layout.setObjectName(u"room_name_layout")
        self.room_name_label = QLabel(self.scroll_area_contents)
        self.room_name_label.setObjectName(u"room_name_label")

        self.room_name_layout.addWidget(self.room_name_label)

        self.room_name_dropdown = QComboBox(self.scroll_area_contents)
        self.room_name_dropdown.setObjectName(u"room_name_dropdown")

        self.room_name_layout.addWidget(self.room_name_dropdown)


        self.verticalLayout.addLayout(self.room_name_layout)

        self.line = QFrame(self.scroll_area_contents)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.verticalLayout.addWidget(self.line)

        self.label_3 = QLabel(self.scroll_area_contents)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.label_3)

        self.health_rotation_layout = QHBoxLayout()
        self.health_rotation_layout.setSpacing(6)
        self.health_rotation_layout.setObjectName(u"health_rotation_layout")
        self.custom_health_rotation_label = QLabel(self.scroll_area_contents)
        self.custom_health_rotation_label.setObjectName(u"custom_health_rotation_label")

        self.health_rotation_layout.addWidget(self.custom_health_rotation_label)

        self.custom_health_rotation_field = QSpinBox(self.scroll_area_contents)
        self.custom_health_rotation_field.setObjectName(u"custom_health_rotation_field")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.custom_health_rotation_field.sizePolicy().hasHeightForWidth())
        self.custom_health_rotation_field.setSizePolicy(sizePolicy)
        self.custom_health_rotation_field.setMaximum(360)

        self.health_rotation_layout.addWidget(self.custom_health_rotation_field)

        self.custom_health_rotation_square = QFrame(self.scroll_area_contents)
        self.custom_health_rotation_square.setObjectName(u"custom_health_rotation_square")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.custom_health_rotation_square.sizePolicy().hasHeightForWidth())
        self.custom_health_rotation_square.setSizePolicy(sizePolicy1)
        self.custom_health_rotation_square.setMinimumSize(QSize(22, 22))
        self.custom_health_rotation_square.setFrameShape(QFrame.StyledPanel)
        self.custom_health_rotation_square.setFrameShadow(QFrame.Raised)

        self.health_rotation_layout.addWidget(self.custom_health_rotation_square)


        self.verticalLayout.addLayout(self.health_rotation_layout)

        self.etank_rotation_layout = QHBoxLayout()
        self.etank_rotation_layout.setSpacing(6)
        self.etank_rotation_layout.setObjectName(u"etank_rotation_layout")
        self.custom_etank_rotation_label = QLabel(self.scroll_area_contents)
        self.custom_etank_rotation_label.setObjectName(u"custom_etank_rotation_label")

        self.etank_rotation_layout.addWidget(self.custom_etank_rotation_label)

        self.custom_etank_rotation_field = QSpinBox(self.scroll_area_contents)
        self.custom_etank_rotation_field.setObjectName(u"custom_etank_rotation_field")
        sizePolicy.setHeightForWidth(self.custom_etank_rotation_field.sizePolicy().hasHeightForWidth())
        self.custom_etank_rotation_field.setSizePolicy(sizePolicy)
        self.custom_etank_rotation_field.setMaximum(360)

        self.etank_rotation_layout.addWidget(self.custom_etank_rotation_field)

        self.custom_etank_rotation_square = QFrame(self.scroll_area_contents)
        self.custom_etank_rotation_square.setObjectName(u"custom_etank_rotation_square")
        sizePolicy1.setHeightForWidth(self.custom_etank_rotation_square.sizePolicy().hasHeightForWidth())
        self.custom_etank_rotation_square.setSizePolicy(sizePolicy1)
        self.custom_etank_rotation_square.setMinimumSize(QSize(22, 22))
        self.custom_etank_rotation_square.setFrameShape(QFrame.StyledPanel)
        self.custom_etank_rotation_square.setFrameShadow(QFrame.Raised)

        self.etank_rotation_layout.addWidget(self.custom_etank_rotation_square)


        self.verticalLayout.addLayout(self.etank_rotation_layout)

        self.dna_rotation_layout = QHBoxLayout()
        self.dna_rotation_layout.setSpacing(6)
        self.dna_rotation_layout.setObjectName(u"dna_rotation_layout")
        self.custom_dna_rotation_label = QLabel(self.scroll_area_contents)
        self.custom_dna_rotation_label.setObjectName(u"custom_dna_rotation_label")

        self.dna_rotation_layout.addWidget(self.custom_dna_rotation_label)

        self.custom_dna_rotation_field = QSpinBox(self.scroll_area_contents)
        self.custom_dna_rotation_field.setObjectName(u"custom_dna_rotation_field")
        sizePolicy.setHeightForWidth(self.custom_dna_rotation_field.sizePolicy().hasHeightForWidth())
        self.custom_dna_rotation_field.setSizePolicy(sizePolicy)
        self.custom_dna_rotation_field.setMaximum(360)

        self.dna_rotation_layout.addWidget(self.custom_dna_rotation_field)

        self.custom_dna_rotation_square = QFrame(self.scroll_area_contents)
        self.custom_dna_rotation_square.setObjectName(u"custom_dna_rotation_square")
        sizePolicy1.setHeightForWidth(self.custom_dna_rotation_square.sizePolicy().hasHeightForWidth())
        self.custom_dna_rotation_square.setSizePolicy(sizePolicy1)
        self.custom_dna_rotation_square.setMinimumSize(QSize(22, 22))
        self.custom_dna_rotation_square.setFrameShape(QFrame.StyledPanel)
        self.custom_dna_rotation_square.setFrameShadow(QFrame.Raised)

        self.dna_rotation_layout.addWidget(self.custom_dna_rotation_square)


        self.verticalLayout.addLayout(self.dna_rotation_layout)

        self.line_2 = QFrame(self.scroll_area_contents)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.HLine)
        self.line_2.setFrameShadow(QFrame.Sunken)

        self.verticalLayout.addWidget(self.line_2)

        self.label_2 = QLabel(self.scroll_area_contents)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.label_2)

        self.music_sub_label = QLabel(self.scroll_area_contents)
        self.music_sub_label.setObjectName(u"music_sub_label")
        self.music_sub_label.setAlignment(Qt.AlignCenter)
        self.music_sub_label.setWordWrap(True)

        self.verticalLayout.addWidget(self.music_sub_label)

        self.vanilla_music_option = QRadioButton(self.scroll_area_contents)
        self.vanilla_music_option.setObjectName(u"vanilla_music_option")
        self.vanilla_music_option.setChecked(True)

        self.verticalLayout.addWidget(self.vanilla_music_option)

        self.vanilla_music_label = QLabel(self.scroll_area_contents)
        self.vanilla_music_label.setObjectName(u"vanilla_music_label")
        self.vanilla_music_label.setWordWrap(True)

        self.verticalLayout.addWidget(self.vanilla_music_label)

        self.type_music_option = QRadioButton(self.scroll_area_contents)
        self.type_music_option.setObjectName(u"type_music_option")

        self.verticalLayout.addWidget(self.type_music_option)

        self.type_music_label = QLabel(self.scroll_area_contents)
        self.type_music_label.setObjectName(u"type_music_label")
        self.type_music_label.setAlignment(Qt.AlignJustify|Qt.AlignVCenter)
        self.type_music_label.setWordWrap(True)

        self.verticalLayout.addWidget(self.type_music_label)

        self.full_music_option = QRadioButton(self.scroll_area_contents)
        self.full_music_option.setObjectName(u"full_music_option")

        self.verticalLayout.addWidget(self.full_music_option)

        self.full_music_label = QLabel(self.scroll_area_contents)
        self.full_music_label.setObjectName(u"full_music_label")
        self.full_music_label.setWordWrap(True)

        self.verticalLayout.addWidget(self.full_music_label)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.scrollArea.setWidget(self.scroll_area_contents)

        self.gridLayout.addWidget(self.scrollArea, 1, 0, 1, 3)


        self.retranslateUi(AM2RCosmeticPatchesDialog)

        QMetaObject.connectSlotsByName(AM2RCosmeticPatchesDialog)
    # setupUi

    def retranslateUi(self, AM2RCosmeticPatchesDialog):
        AM2RCosmeticPatchesDialog.setWindowTitle(QCoreApplication.translate("AM2RCosmeticPatchesDialog", u"AM2R - Cosmetic Options", None))
        self.accept_button.setText(QCoreApplication.translate("AM2RCosmeticPatchesDialog", u"Accept", None))
        self.reset_button.setText(QCoreApplication.translate("AM2RCosmeticPatchesDialog", u"Reset to Defaults", None))
        self.cancel_button.setText(QCoreApplication.translate("AM2RCosmeticPatchesDialog", u"Cancel", None))
        self.label.setText(QCoreApplication.translate("AM2RCosmeticPatchesDialog", u"Game Changes", None))
        self.show_unexplored_map_check.setText(QCoreApplication.translate("AM2RCosmeticPatchesDialog", u"Show fully unexplored map by default", None))
        self.show_unexplored_map_label.setText(QCoreApplication.translate("AM2RCosmeticPatchesDialog", u"Makes you start with a map, which shows unexplored pickups and non-visited tiles as gray.", None))
        self.unveiled_blocks_check.setText(QCoreApplication.translate("AM2RCosmeticPatchesDialog", u"Unveil breakable blocks from the start", None))
        self.unveiled_blocks_label.setText(QCoreApplication.translate("AM2RCosmeticPatchesDialog", u"Blocks that normally need bombs to get unveiled, are now unveiled from the start.", None))
        self.room_name_label.setText(QCoreApplication.translate("AM2RCosmeticPatchesDialog", u"Show Room Names on HUD", None))
        self.label_3.setText(QCoreApplication.translate("AM2RCosmeticPatchesDialog", u"Graphics", None))
        self.custom_health_rotation_label.setText(QCoreApplication.translate("AM2RCosmeticPatchesDialog", u"Health HUD color rotation", None))
        self.custom_etank_rotation_label.setText(QCoreApplication.translate("AM2RCosmeticPatchesDialog", u"E-Tank HUD color rotation", None))
        self.custom_dna_rotation_label.setText(QCoreApplication.translate("AM2RCosmeticPatchesDialog", u"DNA HUD color rotation", None))
        self.label_2.setText(QCoreApplication.translate("AM2RCosmeticPatchesDialog", u"Music", None))
        self.music_sub_label.setText(QCoreApplication.translate("AM2RCosmeticPatchesDialog", u"Changes how music is shuffled.", None))
        self.vanilla_music_option.setText(QCoreApplication.translate("AM2RCosmeticPatchesDialog", u"Vanilla", None))
        self.vanilla_music_label.setText(QCoreApplication.translate("AM2RCosmeticPatchesDialog", u"Does not shuffle any songs.", None))
        self.type_music_option.setText(QCoreApplication.translate("AM2RCosmeticPatchesDialog", u"Per Type", None))
        self.type_music_label.setText(QCoreApplication.translate("AM2RCosmeticPatchesDialog", u"Only shuffles songs within certain types, those being \"combat\", \"exploration\" and \"fanfares\". This ensures that you won't be hearing boss music while trying to explore an area. Certain songs, such as the Credits song are exempt from shuffling.", None))
        self.full_music_option.setText(QCoreApplication.translate("AM2RCosmeticPatchesDialog", u"Full Random", None))
        self.full_music_label.setText(QCoreApplication.translate("AM2RCosmeticPatchesDialog", u"Will shuffle all songs. Note: due to how the game works, it's very likely for the music to bug out at Metroid fights.", None))
    # retranslateUi

