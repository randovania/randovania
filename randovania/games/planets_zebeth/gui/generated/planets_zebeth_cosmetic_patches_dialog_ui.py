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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog,
    QFrame, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

class Ui_PlanetsZebethCosmeticPatchesDialog(object):
    def setupUi(self, PlanetsZebethCosmeticPatchesDialog):
        if not PlanetsZebethCosmeticPatchesDialog.objectName():
            PlanetsZebethCosmeticPatchesDialog.setObjectName(u"PlanetsZebethCosmeticPatchesDialog")
        PlanetsZebethCosmeticPatchesDialog.resize(437, 405)
        self.verticalLayout_2 = QVBoxLayout(PlanetsZebethCosmeticPatchesDialog)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.scrollArea = QScrollArea(PlanetsZebethCosmeticPatchesDialog)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.scroll_area_contents = QWidget()
        self.scroll_area_contents.setObjectName(u"scroll_area_contents")
        self.scroll_area_contents.setGeometry(QRect(0, 0, 435, 357))
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

        self.use_sm_boss_theme_check = QCheckBox(self.scroll_area_contents)
        self.use_sm_boss_theme_check.setObjectName(u"use_sm_boss_theme_check")

        self.verticalLayout.addWidget(self.use_sm_boss_theme_check)

        self.use_sm_boss_theme_label = QLabel(self.scroll_area_contents)
        self.use_sm_boss_theme_label.setObjectName(u"use_sm_boss_theme_label")
        self.use_sm_boss_theme_label.setTextFormat(Qt.TextFormat.AutoText)
        self.use_sm_boss_theme_label.setWordWrap(True)

        self.verticalLayout.addWidget(self.use_sm_boss_theme_label)

        self.use_alternative_escape_theme_check = QCheckBox(self.scroll_area_contents)
        self.use_alternative_escape_theme_check.setObjectName(u"use_alternative_escape_theme_check")

        self.verticalLayout.addWidget(self.use_alternative_escape_theme_check)

        self.use_alternative_escape_theme_label = QLabel(self.scroll_area_contents)
        self.use_alternative_escape_theme_label.setObjectName(u"use_alternative_escape_theme_label")
        self.use_alternative_escape_theme_label.setWordWrap(True)

        self.verticalLayout.addWidget(self.use_alternative_escape_theme_label)

        self.scrollArea.setWidget(self.scroll_area_contents)

        self.verticalLayout_2.addWidget(self.scrollArea)

        self.line = QFrame(PlanetsZebethCosmeticPatchesDialog)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_2.addWidget(self.line)

        self.footer_layout = QHBoxLayout()
        self.footer_layout.setSpacing(6)
        self.footer_layout.setObjectName(u"footer_layout")
        self.footer_layout.setContentsMargins(6, 6, 6, 6)
        self.reset_button = QPushButton(PlanetsZebethCosmeticPatchesDialog)
        self.reset_button.setObjectName(u"reset_button")
        self.reset_button.setText(u"\u2b8c Reset to Defaults")

        self.footer_layout.addWidget(self.reset_button)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.footer_layout.addItem(self.horizontalSpacer)

        self.accept_button = QPushButton(PlanetsZebethCosmeticPatchesDialog)
        self.accept_button.setObjectName(u"accept_button")
        self.accept_button.setMinimumSize(QSize(96, 0))
        self.accept_button.setText(u"\U0001f5f8 Accept")

        self.footer_layout.addWidget(self.accept_button)

        self.cancel_button = QPushButton(PlanetsZebethCosmeticPatchesDialog)
        self.cancel_button.setObjectName(u"cancel_button")
        self.cancel_button.setMinimumSize(QSize(96, 0))
        self.cancel_button.setText(u"\U0001f6c7 Cancel")

        self.footer_layout.addWidget(self.cancel_button)


        self.verticalLayout_2.addLayout(self.footer_layout)


        self.retranslateUi(PlanetsZebethCosmeticPatchesDialog)

        self.accept_button.setDefault(True)


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

