# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_am2r_energy.ui'
##
## Created by: Qt User Interface Compiler version 6.7.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import *  # type: ignore
from PySide6.QtGui import *  # type: ignore
from PySide6.QtWidgets import *  # type: ignore

class Ui_PresetAM2REnergy(object):
    def setupUi(self, PresetAM2REnergy):
        if not PresetAM2REnergy.objectName():
            PresetAM2REnergy.setObjectName(u"PresetAM2REnergy")
        PresetAM2REnergy.resize(514, 434)
        self.centralWidget = QWidget(PresetAM2REnergy)
        self.centralWidget.setObjectName(u"centralWidget")
        self.centralWidget.setMaximumSize(QSize(16777215, 16777215))
        self.main_layout = QVBoxLayout(self.centralWidget)
        self.main_layout.setSpacing(6)
        self.main_layout.setContentsMargins(11, 11, 11, 11)
        self.main_layout.setObjectName(u"main_layout")
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_area = QScrollArea(self.centralWidget)
        self.scroll_area.setObjectName(u"scroll_area")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area_contents = QWidget()
        self.scroll_area_contents.setObjectName(u"scroll_area_contents")
        self.scroll_area_contents.setGeometry(QRect(0, 0, 512, 432))
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scroll_area_contents.sizePolicy().hasHeightForWidth())
        self.scroll_area_contents.setSizePolicy(sizePolicy)
        self.scroll_area_layout = QVBoxLayout(self.scroll_area_contents)
        self.scroll_area_layout.setSpacing(6)
        self.scroll_area_layout.setContentsMargins(11, 11, 11, 11)
        self.scroll_area_layout.setObjectName(u"scroll_area_layout")
        self.scroll_area_layout.setContentsMargins(1, 1, 1, 0)
        self.energy_tank_box = QGroupBox(self.scroll_area_contents)
        self.energy_tank_box.setObjectName(u"energy_tank_box")
        self.gridLayout_2 = QGridLayout(self.energy_tank_box)
        self.gridLayout_2.setSpacing(6)
        self.gridLayout_2.setContentsMargins(11, 11, 11, 11)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.energy_tank_capacity_spin_box = QSpinBox(self.energy_tank_box)
        self.energy_tank_capacity_spin_box.setObjectName(u"energy_tank_capacity_spin_box")
        self.energy_tank_capacity_spin_box.setMinimum(2)
        self.energy_tank_capacity_spin_box.setMaximum(1000)
        self.energy_tank_capacity_spin_box.setValue(100)

        self.gridLayout_2.addWidget(self.energy_tank_capacity_spin_box, 2, 1, 1, 1)

        self.energy_tank_capacity_label = QLabel(self.energy_tank_box)
        self.energy_tank_capacity_label.setObjectName(u"energy_tank_capacity_label")

        self.gridLayout_2.addWidget(self.energy_tank_capacity_label, 2, 0, 1, 1)

        self.energy_tank_capacity_description = QLabel(self.energy_tank_box)
        self.energy_tank_capacity_description.setObjectName(u"energy_tank_capacity_description")
        self.energy_tank_capacity_description.setWordWrap(True)

        self.gridLayout_2.addWidget(self.energy_tank_capacity_description, 0, 0, 1, 2)

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

        self.energy_tank_spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.scroll_area_layout.addItem(self.energy_tank_spacer)

        self.scroll_area.setWidget(self.scroll_area_contents)

        self.main_layout.addWidget(self.scroll_area)

        PresetAM2REnergy.setCentralWidget(self.centralWidget)

        self.retranslateUi(PresetAM2REnergy)

        QMetaObject.connectSlotsByName(PresetAM2REnergy)
    # setupUi

    def retranslateUi(self, PresetAM2REnergy):
        PresetAM2REnergy.setWindowTitle(QCoreApplication.translate("PresetAM2REnergy", u"Energy", None))
        self.energy_tank_box.setTitle(QCoreApplication.translate("PresetAM2REnergy", u"Energy tank", None))
        self.energy_tank_capacity_spin_box.setSuffix(QCoreApplication.translate("PresetAM2REnergy", u" energy", None))
        self.energy_tank_capacity_label.setText(QCoreApplication.translate("PresetAM2REnergy", u"Energy per tank", None))
        self.energy_tank_capacity_description.setText(QCoreApplication.translate("PresetAM2REnergy", u"<html><head/><body><p>Configure how much energy each Energy Tank you collect will provide. Your base energy is always this quantity, minus 1.</p><p>While logic will respect this value, only the original value (100) has been tested.</p></body></html>", None))
        self.suit_dr_box.setTitle(QCoreApplication.translate("PresetAM2REnergy", u"Suit Damage Reduction", None))
        self.first_suit_label.setText(QCoreApplication.translate("PresetAM2REnergy", u"First Suit Damage Reduction", None))
        self.suit_dr_description.setText(QCoreApplication.translate("PresetAM2REnergy", u"<html><head/><body><p>Configure Damage Reduction for suit count. AM2R only cares about suit count not order.</p><p>0% will make you take full damage (equal to suitless). 100% will make you take no damage.</p><p>While logic will respect this value, only the vanilla values (50%, 75%) have been tested.</p></body></html>", None))
        self.first_suit_spin_box.setSuffix(QCoreApplication.translate("PresetAM2REnergy", u"%", None))
        self.second_suit_spin_box.setSuffix(QCoreApplication.translate("PresetAM2REnergy", u"%", None))
        self.second_suit_label.setText(QCoreApplication.translate("PresetAM2REnergy", u"Second Suit Damage Reduction", None))
    # retranslateUi

