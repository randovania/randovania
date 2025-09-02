# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_am2r_gameplay.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QGridLayout, QGroupBox,
    QLabel, QMainWindow, QScrollArea, QSizePolicy,
    QSpacerItem, QSpinBox, QVBoxLayout, QWidget)

class Ui_PresetAM2RGameplay(object):
    def setupUi(self, PresetAM2RGameplay):
        if not PresetAM2RGameplay.objectName():
            PresetAM2RGameplay.setObjectName(u"PresetAM2RGameplay")
        PresetAM2RGameplay.resize(528, 582)
        self.centralWidget = QWidget(PresetAM2RGameplay)
        self.centralWidget.setObjectName(u"centralWidget")
        self.centralWidget.setMaximumSize(QSize(16777215, 16777215))
        self.main_layout = QVBoxLayout(self.centralWidget)
        self.main_layout.setSpacing(6)
        self.main_layout.setContentsMargins(11, 11, 11, 11)
        self.main_layout.setObjectName(u"main_layout")
        self.main_layout.setContentsMargins(6, 6, 6, 6)
        self.scroll_area = QScrollArea(self.centralWidget)
        self.scroll_area.setObjectName(u"scroll_area")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area_contents = QWidget()
        self.scroll_area_contents.setObjectName(u"scroll_area_contents")
        self.scroll_area_contents.setGeometry(QRect(0, -408, 495, 978))
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scroll_area_contents.sizePolicy().hasHeightForWidth())
        self.scroll_area_contents.setSizePolicy(sizePolicy)
        self.scroll_area_layout = QVBoxLayout(self.scroll_area_contents)
        self.scroll_area_layout.setSpacing(6)
        self.scroll_area_layout.setContentsMargins(11, 11, 11, 11)
        self.scroll_area_layout.setObjectName(u"scroll_area_layout")
        self.scroll_area_layout.setContentsMargins(6, 6, 6, 6)
        self.misc_box = QGroupBox(self.scroll_area_contents)
        self.misc_box.setObjectName(u"misc_box")
        self.verticalLayout = QVBoxLayout(self.misc_box)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.skip_cutscenes_check = QCheckBox(self.misc_box)
        self.skip_cutscenes_check.setObjectName(u"skip_cutscenes_check")

        self.verticalLayout.addWidget(self.skip_cutscenes_check)

        self.skip_cutscenes_label = QLabel(self.misc_box)
        self.skip_cutscenes_label.setObjectName(u"skip_cutscenes_label")
        self.skip_cutscenes_label.setWordWrap(True)

        self.verticalLayout.addWidget(self.skip_cutscenes_label)

        self.skip_save_cutscene_check = QCheckBox(self.misc_box)
        self.skip_save_cutscene_check.setObjectName(u"skip_save_cutscene_check")

        self.verticalLayout.addWidget(self.skip_save_cutscene_check)

        self.skip_save_cutscene_label = QLabel(self.misc_box)
        self.skip_save_cutscene_label.setObjectName(u"skip_save_cutscene_label")
        self.skip_save_cutscene_label.setWordWrap(True)

        self.verticalLayout.addWidget(self.skip_save_cutscene_label)

        self.skip_item_cutscenes_check = QCheckBox(self.misc_box)
        self.skip_item_cutscenes_check.setObjectName(u"skip_item_cutscenes_check")

        self.verticalLayout.addWidget(self.skip_item_cutscenes_check)

        self.skip_item_cutscenes_label = QLabel(self.misc_box)
        self.skip_item_cutscenes_label.setObjectName(u"skip_item_cutscenes_label")
        self.skip_item_cutscenes_label.setWordWrap(True)

        self.verticalLayout.addWidget(self.skip_item_cutscenes_label)

        self.fusion_mode_check = QCheckBox(self.misc_box)
        self.fusion_mode_check.setObjectName(u"fusion_mode_check")

        self.verticalLayout.addWidget(self.fusion_mode_check)

        self.fusion_mode_label = QLabel(self.misc_box)
        self.fusion_mode_label.setObjectName(u"fusion_mode_label")
        self.fusion_mode_label.setWordWrap(True)

        self.verticalLayout.addWidget(self.fusion_mode_label)


        self.scroll_area_layout.addWidget(self.misc_box)

        self.energy_tank_box = QGroupBox(self.scroll_area_contents)
        self.energy_tank_box.setObjectName(u"energy_tank_box")
        self.gridLayout_2 = QGridLayout(self.energy_tank_box)
        self.gridLayout_2.setSpacing(6)
        self.gridLayout_2.setContentsMargins(11, 11, 11, 11)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.energy_tank_capacity_description = QLabel(self.energy_tank_box)
        self.energy_tank_capacity_description.setObjectName(u"energy_tank_capacity_description")
        self.energy_tank_capacity_description.setWordWrap(True)

        self.gridLayout_2.addWidget(self.energy_tank_capacity_description, 0, 0, 1, 2)

        self.energy_tank_capacity_spin_box = QSpinBox(self.energy_tank_box)
        self.energy_tank_capacity_spin_box.setObjectName(u"energy_tank_capacity_spin_box")
        self.energy_tank_capacity_spin_box.setMinimum(2)
        self.energy_tank_capacity_spin_box.setMaximum(1000)
        self.energy_tank_capacity_spin_box.setValue(100)

        self.gridLayout_2.addWidget(self.energy_tank_capacity_spin_box, 2, 1, 1, 1)

        self.energy_tank_capacity_label = QLabel(self.energy_tank_box)
        self.energy_tank_capacity_label.setObjectName(u"energy_tank_capacity_label")

        self.gridLayout_2.addWidget(self.energy_tank_capacity_label, 2, 0, 1, 1)

        self.energy_tank_capacity_spacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.gridLayout_2.addItem(self.energy_tank_capacity_spacer, 1, 0, 1, 2)


        self.scroll_area_layout.addWidget(self.energy_tank_box)

        self.suit_dr_box = QGroupBox(self.scroll_area_contents)
        self.suit_dr_box.setObjectName(u"suit_dr_box")
        self.constant_environment_damage_layout = QGridLayout(self.suit_dr_box)
        self.constant_environment_damage_layout.setSpacing(6)
        self.constant_environment_damage_layout.setContentsMargins(11, 11, 11, 11)
        self.constant_environment_damage_layout.setObjectName(u"constant_environment_damage_layout")
        self.first_suit_label = QLabel(self.suit_dr_box)
        self.first_suit_label.setObjectName(u"first_suit_label")

        self.constant_environment_damage_layout.addWidget(self.first_suit_label, 5, 0, 1, 1)

        self.suit_dr_description = QLabel(self.suit_dr_box)
        self.suit_dr_description.setObjectName(u"suit_dr_description")
        self.suit_dr_description.setWordWrap(True)

        self.constant_environment_damage_layout.addWidget(self.suit_dr_description, 4, 0, 1, 2)

        self.first_suit_spin_box = QSpinBox(self.suit_dr_box)
        self.first_suit_spin_box.setObjectName(u"first_suit_spin_box")
        self.first_suit_spin_box.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)
        self.first_suit_spin_box.setMinimum(0)
        self.first_suit_spin_box.setMaximum(100)
        self.first_suit_spin_box.setValue(50)

        self.constant_environment_damage_layout.addWidget(self.first_suit_spin_box, 5, 1, 1, 1)

        self.second_suit_spin_box = QSpinBox(self.suit_dr_box)
        self.second_suit_spin_box.setObjectName(u"second_suit_spin_box")
        self.second_suit_spin_box.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)
        self.second_suit_spin_box.setMinimum(0)
        self.second_suit_spin_box.setMaximum(100)
        self.second_suit_spin_box.setValue(75)

        self.constant_environment_damage_layout.addWidget(self.second_suit_spin_box, 6, 1, 1, 1)

        self.second_suit_label = QLabel(self.suit_dr_box)
        self.second_suit_label.setObjectName(u"second_suit_label")

        self.constant_environment_damage_layout.addWidget(self.second_suit_label, 6, 0, 1, 1)


        self.scroll_area_layout.addWidget(self.suit_dr_box)

        self.flipping_box = QGroupBox(self.scroll_area_contents)
        self.flipping_box.setObjectName(u"flipping_box")
        self.verticalLayout_2 = QVBoxLayout(self.flipping_box)
        self.verticalLayout_2.setSpacing(6)
        self.verticalLayout_2.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.flipping_label = QLabel(self.flipping_box)
        self.flipping_label.setObjectName(u"flipping_label")
        self.flipping_label.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.flipping_label)

        self.horizontally_flip_gameplay_check = QCheckBox(self.flipping_box)
        self.horizontally_flip_gameplay_check.setObjectName(u"horizontally_flip_gameplay_check")

        self.verticalLayout_2.addWidget(self.horizontally_flip_gameplay_check)

        self.vertically_flip_gameplay_check = QCheckBox(self.flipping_box)
        self.vertically_flip_gameplay_check.setObjectName(u"vertically_flip_gameplay_check")

        self.verticalLayout_2.addWidget(self.vertically_flip_gameplay_check)


        self.scroll_area_layout.addWidget(self.flipping_box)

        self.energy_tank_spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.scroll_area_layout.addItem(self.energy_tank_spacer)

        self.scroll_area.setWidget(self.scroll_area_contents)

        self.main_layout.addWidget(self.scroll_area)

        PresetAM2RGameplay.setCentralWidget(self.centralWidget)

        self.retranslateUi(PresetAM2RGameplay)

        QMetaObject.connectSlotsByName(PresetAM2RGameplay)
    # setupUi

    def retranslateUi(self, PresetAM2RGameplay):
        PresetAM2RGameplay.setWindowTitle(QCoreApplication.translate("PresetAM2RGameplay", u"Energy", None))
        self.misc_box.setTitle(QCoreApplication.translate("PresetAM2RGameplay", u"Gameplay", None))
        self.skip_cutscenes_check.setText(QCoreApplication.translate("PresetAM2RGameplay", u"Skip gameplay cutscenes", None))
        self.skip_cutscenes_label.setText(QCoreApplication.translate("PresetAM2RGameplay", u"Enabling this will skip most gameplay related cutscenes, such as the Drill Sequence, the cutscenes you'll see when viewing a Metroid for the first time and similar.", None))
        self.skip_save_cutscene_check.setText(QCoreApplication.translate("PresetAM2RGameplay", u"Skip Save Station cutscene", None))
        self.skip_save_cutscene_label.setText(QCoreApplication.translate("PresetAM2RGameplay", u"Enabling this will skip the short cutscene that appears when saving at a Save Station.", None))
        self.skip_item_cutscenes_check.setText(QCoreApplication.translate("PresetAM2RGameplay", u"Skip item acquisition cutscenes", None))
        self.skip_item_cutscenes_label.setText(QCoreApplication.translate("PresetAM2RGameplay", u"Enabling this will skip item related cutscenes, such as the pause when collecting an item or the cutscene that plays when collecting a suit.", None))
        self.fusion_mode_check.setText(QCoreApplication.translate("PresetAM2RGameplay", u"Enable Fusion Mode", None))
        self.fusion_mode_label.setText(QCoreApplication.translate("PresetAM2RGameplay", u"<html><head/><body><p>Fusion Mode enables the Fusion Suit for Samus, makes organic enemies drop X, makes bosses spawn Core-X and makes Metroids move faster.<br/>It does <span style=\" font-weight:600;\">not</span> add a 4x damage multiplier.</p></body></html>", None))
        self.energy_tank_box.setTitle(QCoreApplication.translate("PresetAM2RGameplay", u"Energy Tank", None))
        self.energy_tank_capacity_description.setText(QCoreApplication.translate("PresetAM2RGameplay", u"<html><head/><body><p>Configure how much energy each Energy Tank you collect will provide. Your base energy is always this quantity, minus 1.</p><p>While logic will respect this value, only the original value (100) has been tested.</p></body></html>", None))
        self.energy_tank_capacity_spin_box.setSuffix(QCoreApplication.translate("PresetAM2RGameplay", u" energy", None))
        self.energy_tank_capacity_label.setText(QCoreApplication.translate("PresetAM2RGameplay", u"Energy per tank", None))
        self.suit_dr_box.setTitle(QCoreApplication.translate("PresetAM2RGameplay", u"Suit Damage Reduction", None))
        self.first_suit_label.setText(QCoreApplication.translate("PresetAM2RGameplay", u"First Suit Damage Reduction", None))
        self.suit_dr_description.setText(QCoreApplication.translate("PresetAM2RGameplay", u"<html><head/><body><p>Configure Damage Reduction for suit count. AM2R only cares about suit count not order.<br/>0% will make you take full damage (equal to suitless). 100% will make you take no damage.<br/>While logic will respect this value, only the vanilla values (50%, 75%) have been tested.</p></body></html>", None))
        self.first_suit_spin_box.setSuffix(QCoreApplication.translate("PresetAM2RGameplay", u"%", None))
        self.second_suit_spin_box.setSuffix(QCoreApplication.translate("PresetAM2RGameplay", u"%", None))
        self.second_suit_label.setText(QCoreApplication.translate("PresetAM2RGameplay", u"Second Suit Damage Reduction", None))
        self.flipping_box.setTitle(QCoreApplication.translate("PresetAM2RGameplay", u"Mirroring and Flipping", None))
        self.flipping_label.setText(QCoreApplication.translate("PresetAM2RGameplay", u"These flip the gameplay horizontally, to achieve a mirrored game effect, or vertically, to achieve an upside down effect. They can be combined together.", None))
        self.horizontally_flip_gameplay_check.setText(QCoreApplication.translate("PresetAM2RGameplay", u"Horizontally flip gameplay", None))
        self.vertically_flip_gameplay_check.setText(QCoreApplication.translate("PresetAM2RGameplay", u"Vertically flip gameplay", None))
    # retranslateUi

