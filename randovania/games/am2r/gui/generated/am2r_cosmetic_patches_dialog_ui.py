# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'am2r_cosmetic_patches_dialog.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFrame,
    QHBoxLayout, QLabel, QRadioButton, QSizePolicy,
    QSpacerItem, QSpinBox, QVBoxLayout, QWidget)

class Ui_AM2RCosmeticPatchesDialog(object):
    def setupUi(self, AM2RCosmeticPatchesDialog):
        if not AM2RCosmeticPatchesDialog.objectName():
            AM2RCosmeticPatchesDialog.setObjectName(u"AM2RCosmeticPatchesDialog")
        AM2RCosmeticPatchesDialog.resize(548, 634)
        self.verticalLayout_2 = QVBoxLayout(AM2RCosmeticPatchesDialog)
        self.verticalLayout_2.setSpacing(6)
        self.verticalLayout_2.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel(AM2RCosmeticPatchesDialog)
        self.label.setObjectName(u"label")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_2.addWidget(self.label)

        self.show_unexplored_map_check = QCheckBox(AM2RCosmeticPatchesDialog)
        self.show_unexplored_map_check.setObjectName(u"show_unexplored_map_check")

        self.verticalLayout_2.addWidget(self.show_unexplored_map_check)

        self.show_unexplored_map_label = QLabel(AM2RCosmeticPatchesDialog)
        self.show_unexplored_map_label.setObjectName(u"show_unexplored_map_label")
        self.show_unexplored_map_label.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.show_unexplored_map_label)

        self.unveiled_blocks_check = QCheckBox(AM2RCosmeticPatchesDialog)
        self.unveiled_blocks_check.setObjectName(u"unveiled_blocks_check")

        self.verticalLayout_2.addWidget(self.unveiled_blocks_check)

        self.unveiled_blocks_label = QLabel(AM2RCosmeticPatchesDialog)
        self.unveiled_blocks_label.setObjectName(u"unveiled_blocks_label")
        self.unveiled_blocks_label.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.unveiled_blocks_label)

        self.room_name_layout = QHBoxLayout()
        self.room_name_layout.setSpacing(6)
        self.room_name_layout.setObjectName(u"room_name_layout")
        self.room_name_label = QLabel(AM2RCosmeticPatchesDialog)
        self.room_name_label.setObjectName(u"room_name_label")

        self.room_name_layout.addWidget(self.room_name_label)

        self.room_name_dropdown = QComboBox(AM2RCosmeticPatchesDialog)
        self.room_name_dropdown.setObjectName(u"room_name_dropdown")

        self.room_name_layout.addWidget(self.room_name_dropdown)


        self.verticalLayout_2.addLayout(self.room_name_layout)

        self.line = QFrame(AM2RCosmeticPatchesDialog)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_2.addWidget(self.line)

        self.label_3 = QLabel(AM2RCosmeticPatchesDialog)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_2.addWidget(self.label_3)

        self.health_rotation_layout = QHBoxLayout()
        self.health_rotation_layout.setSpacing(6)
        self.health_rotation_layout.setObjectName(u"health_rotation_layout")
        self.custom_health_rotation_label = QLabel(AM2RCosmeticPatchesDialog)
        self.custom_health_rotation_label.setObjectName(u"custom_health_rotation_label")

        self.health_rotation_layout.addWidget(self.custom_health_rotation_label)

        self.custom_health_rotation_field = QSpinBox(AM2RCosmeticPatchesDialog)
        self.custom_health_rotation_field.setObjectName(u"custom_health_rotation_field")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.custom_health_rotation_field.sizePolicy().hasHeightForWidth())
        self.custom_health_rotation_field.setSizePolicy(sizePolicy)
        self.custom_health_rotation_field.setMaximum(360)

        self.health_rotation_layout.addWidget(self.custom_health_rotation_field)

        self.custom_health_rotation_square = QFrame(AM2RCosmeticPatchesDialog)
        self.custom_health_rotation_square.setObjectName(u"custom_health_rotation_square")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.custom_health_rotation_square.sizePolicy().hasHeightForWidth())
        self.custom_health_rotation_square.setSizePolicy(sizePolicy1)
        self.custom_health_rotation_square.setMinimumSize(QSize(22, 22))
        self.custom_health_rotation_square.setFrameShape(QFrame.Shape.StyledPanel)
        self.custom_health_rotation_square.setFrameShadow(QFrame.Shadow.Raised)

        self.health_rotation_layout.addWidget(self.custom_health_rotation_square)


        self.verticalLayout_2.addLayout(self.health_rotation_layout)

        self.etank_rotation_layout = QHBoxLayout()
        self.etank_rotation_layout.setSpacing(6)
        self.etank_rotation_layout.setObjectName(u"etank_rotation_layout")
        self.custom_etank_rotation_label = QLabel(AM2RCosmeticPatchesDialog)
        self.custom_etank_rotation_label.setObjectName(u"custom_etank_rotation_label")

        self.etank_rotation_layout.addWidget(self.custom_etank_rotation_label)

        self.custom_etank_rotation_field = QSpinBox(AM2RCosmeticPatchesDialog)
        self.custom_etank_rotation_field.setObjectName(u"custom_etank_rotation_field")
        sizePolicy.setHeightForWidth(self.custom_etank_rotation_field.sizePolicy().hasHeightForWidth())
        self.custom_etank_rotation_field.setSizePolicy(sizePolicy)
        self.custom_etank_rotation_field.setMaximum(360)

        self.etank_rotation_layout.addWidget(self.custom_etank_rotation_field)

        self.custom_etank_rotation_square = QFrame(AM2RCosmeticPatchesDialog)
        self.custom_etank_rotation_square.setObjectName(u"custom_etank_rotation_square")
        sizePolicy1.setHeightForWidth(self.custom_etank_rotation_square.sizePolicy().hasHeightForWidth())
        self.custom_etank_rotation_square.setSizePolicy(sizePolicy1)
        self.custom_etank_rotation_square.setMinimumSize(QSize(22, 22))
        self.custom_etank_rotation_square.setFrameShape(QFrame.Shape.StyledPanel)
        self.custom_etank_rotation_square.setFrameShadow(QFrame.Shadow.Raised)

        self.etank_rotation_layout.addWidget(self.custom_etank_rotation_square)


        self.verticalLayout_2.addLayout(self.etank_rotation_layout)

        self.dna_rotation_layout = QHBoxLayout()
        self.dna_rotation_layout.setSpacing(6)
        self.dna_rotation_layout.setObjectName(u"dna_rotation_layout")
        self.custom_dna_rotation_label = QLabel(AM2RCosmeticPatchesDialog)
        self.custom_dna_rotation_label.setObjectName(u"custom_dna_rotation_label")

        self.dna_rotation_layout.addWidget(self.custom_dna_rotation_label)

        self.custom_dna_rotation_field = QSpinBox(AM2RCosmeticPatchesDialog)
        self.custom_dna_rotation_field.setObjectName(u"custom_dna_rotation_field")
        sizePolicy.setHeightForWidth(self.custom_dna_rotation_field.sizePolicy().hasHeightForWidth())
        self.custom_dna_rotation_field.setSizePolicy(sizePolicy)
        self.custom_dna_rotation_field.setMaximum(360)

        self.dna_rotation_layout.addWidget(self.custom_dna_rotation_field)

        self.custom_dna_rotation_square = QFrame(AM2RCosmeticPatchesDialog)
        self.custom_dna_rotation_square.setObjectName(u"custom_dna_rotation_square")
        sizePolicy1.setHeightForWidth(self.custom_dna_rotation_square.sizePolicy().hasHeightForWidth())
        self.custom_dna_rotation_square.setSizePolicy(sizePolicy1)
        self.custom_dna_rotation_square.setMinimumSize(QSize(22, 22))
        self.custom_dna_rotation_square.setFrameShape(QFrame.Shape.StyledPanel)
        self.custom_dna_rotation_square.setFrameShadow(QFrame.Shadow.Raised)

        self.dna_rotation_layout.addWidget(self.custom_dna_rotation_square)


        self.verticalLayout_2.addLayout(self.dna_rotation_layout)

        self.tileset_rotation_layout = QHBoxLayout()
        self.tileset_rotation_layout.setSpacing(6)
        self.tileset_rotation_layout.setObjectName(u"tileset_rotation_layout")
        self.tileset_rotation_label = QLabel(AM2RCosmeticPatchesDialog)
        self.tileset_rotation_label.setObjectName(u"tileset_rotation_label")

        self.tileset_rotation_layout.addWidget(self.tileset_rotation_label)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.tileset_rotation_layout.addItem(self.horizontalSpacer)

        self.tileset_rotation_label_min = QLabel(AM2RCosmeticPatchesDialog)
        self.tileset_rotation_label_min.setObjectName(u"tileset_rotation_label_min")

        self.tileset_rotation_layout.addWidget(self.tileset_rotation_label_min)

        self.tileset_rotation_spinner_min = QSpinBox(AM2RCosmeticPatchesDialog)
        self.tileset_rotation_spinner_min.setObjectName(u"tileset_rotation_spinner_min")
        self.tileset_rotation_spinner_min.setMaximum(360)

        self.tileset_rotation_layout.addWidget(self.tileset_rotation_spinner_min)

        self.tileset_rotation_label_max = QLabel(AM2RCosmeticPatchesDialog)
        self.tileset_rotation_label_max.setObjectName(u"tileset_rotation_label_max")

        self.tileset_rotation_layout.addWidget(self.tileset_rotation_label_max)

        self.tileset_rotation_spinner_max = QSpinBox(AM2RCosmeticPatchesDialog)
        self.tileset_rotation_spinner_max.setObjectName(u"tileset_rotation_spinner_max")
        self.tileset_rotation_spinner_max.setMaximum(360)

        self.tileset_rotation_layout.addWidget(self.tileset_rotation_spinner_max)


        self.verticalLayout_2.addLayout(self.tileset_rotation_layout)

        self.background_rotation_layout = QHBoxLayout()
        self.background_rotation_layout.setSpacing(6)
        self.background_rotation_layout.setObjectName(u"background_rotation_layout")
        self.background_rotation_label = QLabel(AM2RCosmeticPatchesDialog)
        self.background_rotation_label.setObjectName(u"background_rotation_label")

        self.background_rotation_layout.addWidget(self.background_rotation_label)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.background_rotation_layout.addItem(self.horizontalSpacer_4)

        self.background_rotation_label_min = QLabel(AM2RCosmeticPatchesDialog)
        self.background_rotation_label_min.setObjectName(u"background_rotation_label_min")

        self.background_rotation_layout.addWidget(self.background_rotation_label_min)

        self.background_rotation_spinner_min = QSpinBox(AM2RCosmeticPatchesDialog)
        self.background_rotation_spinner_min.setObjectName(u"background_rotation_spinner_min")
        self.background_rotation_spinner_min.setMaximum(360)

        self.background_rotation_layout.addWidget(self.background_rotation_spinner_min)

        self.background_rotation_label_max = QLabel(AM2RCosmeticPatchesDialog)
        self.background_rotation_label_max.setObjectName(u"background_rotation_label_max")

        self.background_rotation_layout.addWidget(self.background_rotation_label_max)

        self.background_rotation_spinner_max = QSpinBox(AM2RCosmeticPatchesDialog)
        self.background_rotation_spinner_max.setObjectName(u"background_rotation_spinner_max")
        self.background_rotation_spinner_max.setMaximum(360)

        self.background_rotation_layout.addWidget(self.background_rotation_spinner_max)


        self.verticalLayout_2.addLayout(self.background_rotation_layout)

        self.line_2 = QFrame(AM2RCosmeticPatchesDialog)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.Shape.HLine)
        self.line_2.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_2.addWidget(self.line_2)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.verticalLayout_2.addItem(self.horizontalSpacer_3)

        self.label_2 = QLabel(AM2RCosmeticPatchesDialog)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_2.addWidget(self.label_2)

        self.music_sub_label = QLabel(AM2RCosmeticPatchesDialog)
        self.music_sub_label.setObjectName(u"music_sub_label")
        self.music_sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.music_sub_label.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.music_sub_label)

        self.vanilla_music_option = QRadioButton(AM2RCosmeticPatchesDialog)
        self.vanilla_music_option.setObjectName(u"vanilla_music_option")
        self.vanilla_music_option.setChecked(True)

        self.verticalLayout_2.addWidget(self.vanilla_music_option)

        self.vanilla_music_label = QLabel(AM2RCosmeticPatchesDialog)
        self.vanilla_music_label.setObjectName(u"vanilla_music_label")
        self.vanilla_music_label.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.vanilla_music_label)

        self.type_music_option = QRadioButton(AM2RCosmeticPatchesDialog)
        self.type_music_option.setObjectName(u"type_music_option")

        self.verticalLayout_2.addWidget(self.type_music_option)

        self.type_music_label = QLabel(AM2RCosmeticPatchesDialog)
        self.type_music_label.setObjectName(u"type_music_label")
        self.type_music_label.setAlignment(Qt.AlignmentFlag.AlignJustify|Qt.AlignmentFlag.AlignVCenter)
        self.type_music_label.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.type_music_label)

        self.full_music_option = QRadioButton(AM2RCosmeticPatchesDialog)
        self.full_music_option.setObjectName(u"full_music_option")

        self.verticalLayout_2.addWidget(self.full_music_option)

        self.full_music_label = QLabel(AM2RCosmeticPatchesDialog)
        self.full_music_label.setObjectName(u"full_music_label")
        self.full_music_label.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.full_music_label)


        self.retranslateUi(AM2RCosmeticPatchesDialog)

        QMetaObject.connectSlotsByName(AM2RCosmeticPatchesDialog)
    # setupUi

    def retranslateUi(self, AM2RCosmeticPatchesDialog):
        AM2RCosmeticPatchesDialog.setWindowTitle(QCoreApplication.translate("AM2RCosmeticPatchesDialog", u"AM2R - Cosmetic Options", None))
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
        self.tileset_rotation_label.setText(QCoreApplication.translate("AM2RCosmeticPatchesDialog", u"Random Tileset color rotation", None))
        self.tileset_rotation_label_min.setText(QCoreApplication.translate("AM2RCosmeticPatchesDialog", u"Min:", None))
        self.tileset_rotation_label_max.setText(QCoreApplication.translate("AM2RCosmeticPatchesDialog", u"Max:", None))
        self.background_rotation_label.setText(QCoreApplication.translate("AM2RCosmeticPatchesDialog", u"Random Background color rotation", None))
        self.background_rotation_label_min.setText(QCoreApplication.translate("AM2RCosmeticPatchesDialog", u"Min:", None))
        self.background_rotation_label_max.setText(QCoreApplication.translate("AM2RCosmeticPatchesDialog", u"Max:", None))
        self.label_2.setText(QCoreApplication.translate("AM2RCosmeticPatchesDialog", u"Music", None))
        self.music_sub_label.setText(QCoreApplication.translate("AM2RCosmeticPatchesDialog", u"Changes how music is shuffled.", None))
        self.vanilla_music_option.setText(QCoreApplication.translate("AM2RCosmeticPatchesDialog", u"Vanilla", None))
        self.vanilla_music_label.setText(QCoreApplication.translate("AM2RCosmeticPatchesDialog", u"Does not shuffle any songs.", None))
        self.type_music_option.setText(QCoreApplication.translate("AM2RCosmeticPatchesDialog", u"Per Type", None))
        self.type_music_label.setText(QCoreApplication.translate("AM2RCosmeticPatchesDialog", u"Only shuffles songs within certain types, those being \"combat\", \"exploration\" and \"fanfares\". This ensures that you won't be hearing boss music while trying to explore an area. Certain songs, such as the Credits song are exempt from shuffling.", None))
        self.full_music_option.setText(QCoreApplication.translate("AM2RCosmeticPatchesDialog", u"Full Random", None))
        self.full_music_label.setText(QCoreApplication.translate("AM2RCosmeticPatchesDialog", u"Will shuffle all songs. Note: due to how the game works, it's very likely for the music to bug out at Metroid fights.", None))
    # retranslateUi

