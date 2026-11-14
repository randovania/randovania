# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'planets_zebeth_cosmetic_patches_dialog.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QHBoxLayout,
    QLabel, QSizePolicy, QVBoxLayout, QWidget)

class Ui_PlanetsZebethCosmeticPatchesDialog(object):
    def setupUi(self, PlanetsZebethCosmeticPatchesDialog):
        if not PlanetsZebethCosmeticPatchesDialog.objectName():
            PlanetsZebethCosmeticPatchesDialog.setObjectName(u"PlanetsZebethCosmeticPatchesDialog")
        PlanetsZebethCosmeticPatchesDialog.resize(437, 405)
        self.verticalLayout_2 = QVBoxLayout(PlanetsZebethCosmeticPatchesDialog)
        self.verticalLayout_2.setSpacing(6)
        self.verticalLayout_2.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.show_unexplored_map_check = QCheckBox(PlanetsZebethCosmeticPatchesDialog)
        self.show_unexplored_map_check.setObjectName(u"show_unexplored_map_check")

        self.verticalLayout_2.addWidget(self.show_unexplored_map_check)

        self.show_unexplored_map_label = QLabel(PlanetsZebethCosmeticPatchesDialog)
        self.show_unexplored_map_label.setObjectName(u"show_unexplored_map_label")
        self.show_unexplored_map_label.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.show_unexplored_map_label)

        self.room_name_layout = QHBoxLayout()
        self.room_name_layout.setSpacing(6)
        self.room_name_layout.setObjectName(u"room_name_layout")
        self.room_name_label = QLabel(PlanetsZebethCosmeticPatchesDialog)
        self.room_name_label.setObjectName(u"room_name_label")

        self.room_name_layout.addWidget(self.room_name_label)

        self.room_name_dropdown = QComboBox(PlanetsZebethCosmeticPatchesDialog)
        self.room_name_dropdown.setObjectName(u"room_name_dropdown")

        self.room_name_layout.addWidget(self.room_name_dropdown)


        self.verticalLayout_2.addLayout(self.room_name_layout)

        self.disable_low_health_beeping_check = QCheckBox(PlanetsZebethCosmeticPatchesDialog)
        self.disable_low_health_beeping_check.setObjectName(u"disable_low_health_beeping_check")

        self.verticalLayout_2.addWidget(self.disable_low_health_beeping_check)

        self.disable_low_health_beeping_label = QLabel(PlanetsZebethCosmeticPatchesDialog)
        self.disable_low_health_beeping_label.setObjectName(u"disable_low_health_beeping_label")

        self.verticalLayout_2.addWidget(self.disable_low_health_beeping_label)

        self.use_sm_boss_theme_check = QCheckBox(PlanetsZebethCosmeticPatchesDialog)
        self.use_sm_boss_theme_check.setObjectName(u"use_sm_boss_theme_check")

        self.verticalLayout_2.addWidget(self.use_sm_boss_theme_check)

        self.use_sm_boss_theme_label = QLabel(PlanetsZebethCosmeticPatchesDialog)
        self.use_sm_boss_theme_label.setObjectName(u"use_sm_boss_theme_label")
        self.use_sm_boss_theme_label.setTextFormat(Qt.TextFormat.AutoText)
        self.use_sm_boss_theme_label.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.use_sm_boss_theme_label)

        self.use_alternative_escape_theme_check = QCheckBox(PlanetsZebethCosmeticPatchesDialog)
        self.use_alternative_escape_theme_check.setObjectName(u"use_alternative_escape_theme_check")

        self.verticalLayout_2.addWidget(self.use_alternative_escape_theme_check)

        self.use_alternative_escape_theme_label = QLabel(PlanetsZebethCosmeticPatchesDialog)
        self.use_alternative_escape_theme_label.setObjectName(u"use_alternative_escape_theme_label")
        self.use_alternative_escape_theme_label.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.use_alternative_escape_theme_label)


        self.retranslateUi(PlanetsZebethCosmeticPatchesDialog)

        QMetaObject.connectSlotsByName(PlanetsZebethCosmeticPatchesDialog)
    # setupUi

    def retranslateUi(self, PlanetsZebethCosmeticPatchesDialog):
        PlanetsZebethCosmeticPatchesDialog.setWindowTitle(QCoreApplication.translate("PlanetsZebethCosmeticPatchesDialog", u"Metroid Planets (Zebeth) - Cosmetic Options", None))
        self.show_unexplored_map_check.setText(QCoreApplication.translate("PlanetsZebethCosmeticPatchesDialog", u"Show fully unexplored map by default", None))
        self.show_unexplored_map_label.setText(QCoreApplication.translate("PlanetsZebethCosmeticPatchesDialog", u"Makes you start with a map, which shows unexplored pickups and non-visited tiles as gray.", None))
        self.room_name_label.setText(QCoreApplication.translate("PlanetsZebethCosmeticPatchesDialog", u"Show Room Names on HUD", None))
        self.disable_low_health_beeping_check.setText(QCoreApplication.translate("PlanetsZebethCosmeticPatchesDialog", u"Disable low health beeping", None))
        self.disable_low_health_beeping_label.setText(QCoreApplication.translate("PlanetsZebethCosmeticPatchesDialog", u"Disables the beeping sound when health is lower than 30 HP.", None))
        self.use_sm_boss_theme_check.setText(QCoreApplication.translate("PlanetsZebethCosmeticPatchesDialog", u"Use Super Metroid boss themes", None))
        self.use_sm_boss_theme_label.setText(QCoreApplication.translate("PlanetsZebethCosmeticPatchesDialog", u"Makes the game play SM boss themes instead of Nestroid boss themes.", None))
        self.use_alternative_escape_theme_check.setText(QCoreApplication.translate("PlanetsZebethCosmeticPatchesDialog", u"Use alternative escape theme", None))
        self.use_alternative_escape_theme_label.setText(QCoreApplication.translate("PlanetsZebethCosmeticPatchesDialog", u"Makes the game play SM escape theme instead of Nestroid escape theme.", None))
    # retranslateUi

