# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'planets_zebeth_cosmetic_patches_dialog.ui'
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
    QGridLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

class Ui_PlanetsZebethCosmeticPatchesDialog(object):
    def setupUi(self, PlanetsZebethCosmeticPatchesDialog):
        if not PlanetsZebethCosmeticPatchesDialog.objectName():
            PlanetsZebethCosmeticPatchesDialog.setObjectName(u"PlanetsZebethCosmeticPatchesDialog")
        PlanetsZebethCosmeticPatchesDialog.resize(437, 389)
        self.gridLayout = QGridLayout(PlanetsZebethCosmeticPatchesDialog)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setContentsMargins(11, 11, 11, 11)
        self.gridLayout.setObjectName(u"gridLayout")
        self.accept_button = QPushButton(PlanetsZebethCosmeticPatchesDialog)
        self.accept_button.setObjectName(u"accept_button")

        self.gridLayout.addWidget(self.accept_button, 2, 0, 1, 1)

        self.reset_button = QPushButton(PlanetsZebethCosmeticPatchesDialog)
        self.reset_button.setObjectName(u"reset_button")

        self.gridLayout.addWidget(self.reset_button, 2, 2, 1, 1)

        self.cancel_button = QPushButton(PlanetsZebethCosmeticPatchesDialog)
        self.cancel_button.setObjectName(u"cancel_button")

        self.gridLayout.addWidget(self.cancel_button, 2, 1, 1, 1)

        self.scrollArea = QScrollArea(PlanetsZebethCosmeticPatchesDialog)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.scroll_area_contents = QWidget()
        self.scroll_area_contents.setObjectName(u"scroll_area_contents")
        self.scroll_area_contents.setGeometry(QRect(0, 0, 417, 337))
        self.verticalLayout = QVBoxLayout(self.scroll_area_contents)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.show_unexplored_map_check = QCheckBox(self.scroll_area_contents)
        self.show_unexplored_map_check.setObjectName(u"show_unexplored_map_check")

        self.verticalLayout.addWidget(self.show_unexplored_map_check)

        self.show_unexplored_map_label = QLabel(self.scroll_area_contents)
        self.show_unexplored_map_label.setObjectName(u"show_unexplored_map_label")
        self.show_unexplored_map_label.setWordWrap(True)

        self.verticalLayout.addWidget(self.show_unexplored_map_label)

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

        self.disable_low_health_beeping_check = QCheckBox(self.scroll_area_contents)
        self.disable_low_health_beeping_check.setObjectName(u"disable_low_health_beeping_check")

        self.verticalLayout.addWidget(self.disable_low_health_beeping_check)

        self.disable_low_health_beeping_label = QLabel(self.scroll_area_contents)
        self.disable_low_health_beeping_label.setObjectName(u"disable_low_health_beeping_label")

        self.verticalLayout.addWidget(self.disable_low_health_beeping_label)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.scrollArea.setWidget(self.scroll_area_contents)

        self.gridLayout.addWidget(self.scrollArea, 1, 0, 1, 3)


        self.retranslateUi(PlanetsZebethCosmeticPatchesDialog)

        self.accept_button.setDefault(True)


        QMetaObject.connectSlotsByName(PlanetsZebethCosmeticPatchesDialog)
    # setupUi

    def retranslateUi(self, PlanetsZebethCosmeticPatchesDialog):
        PlanetsZebethCosmeticPatchesDialog.setWindowTitle(QCoreApplication.translate("PlanetsZebethCosmeticPatchesDialog", u"Metroid Planets (Zebeth) - Cosmetic Options", None))
        self.accept_button.setText(QCoreApplication.translate("PlanetsZebethCosmeticPatchesDialog", u"Accept", None))
        self.reset_button.setText(QCoreApplication.translate("PlanetsZebethCosmeticPatchesDialog", u"Reset to Defaults", None))
        self.cancel_button.setText(QCoreApplication.translate("PlanetsZebethCosmeticPatchesDialog", u"Cancel", None))
        self.show_unexplored_map_check.setText(QCoreApplication.translate("PlanetsZebethCosmeticPatchesDialog", u"Show fully unexplored map by default", None))
        self.show_unexplored_map_label.setText(QCoreApplication.translate("PlanetsZebethCosmeticPatchesDialog", u"Makes you start with a map, which shows unexplored pickups and non-visited tiles as gray.", None))
        self.room_name_label.setText(QCoreApplication.translate("PlanetsZebethCosmeticPatchesDialog", u"Show Room Names on HUD", None))
        self.disable_low_health_beeping_check.setText(QCoreApplication.translate("PlanetsZebethCosmeticPatchesDialog", u"Disable low health beeping", None))
        self.disable_low_health_beeping_label.setText(QCoreApplication.translate("PlanetsZebethCosmeticPatchesDialog", u"Disables the beeping sound when health is lower than 30 HP.", None))
    # retranslateUi

