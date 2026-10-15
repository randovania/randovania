# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_echoes_energy.ui'
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
from PySide6.QtWidgets import (QAbstractSpinBox, QApplication, QCheckBox, QDoubleSpinBox,
    QFrame, QGridLayout, QGroupBox, QLabel,
    QMainWindow, QScrollArea, QSizePolicy, QSpacerItem,
    QSpinBox, QVBoxLayout, QWidget)

class Ui_PresetEchoesEnergy(object):
    def setupUi(self, PresetEchoesEnergy):
        if not PresetEchoesEnergy.objectName():
            PresetEchoesEnergy.setObjectName(u"PresetEchoesEnergy")
        PresetEchoesEnergy.resize(476, 628)
        self.centralWidget = QWidget(PresetEchoesEnergy)
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
        self.scroll_area_contents.setGeometry(QRect(0, 0, 474, 626))
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
        self.energy_tank_capacity_label = QLabel(self.energy_tank_box)
        self.energy_tank_capacity_label.setObjectName(u"energy_tank_capacity_label")

        self.gridLayout_2.addWidget(self.energy_tank_capacity_label, 2, 0, 1, 1)

        self.energy_tank_capacity_spin_box = QSpinBox(self.energy_tank_box)
        self.energy_tank_capacity_spin_box.setObjectName(u"energy_tank_capacity_spin_box")
        self.energy_tank_capacity_spin_box.setMinimum(2)
        self.energy_tank_capacity_spin_box.setMaximum(1000)

        self.gridLayout_2.addWidget(self.energy_tank_capacity_spin_box, 2, 1, 1, 1)

        self.dangerous_tank_check = QCheckBox(self.energy_tank_box)
        self.dangerous_tank_check.setObjectName(u"dangerous_tank_check")

        self.gridLayout_2.addWidget(self.dangerous_tank_check, 4, 0, 1, 2)

        self.line = QFrame(self.energy_tank_box)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout_2.addWidget(self.line, 3, 0, 1, 2)

        self.energy_tank_capacity_spacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.gridLayout_2.addItem(self.energy_tank_capacity_spacer, 1, 0, 1, 2)

        self.energy_tank_capacity_description = QLabel(self.energy_tank_box)
        self.energy_tank_capacity_description.setObjectName(u"energy_tank_capacity_description")
        self.energy_tank_capacity_description.setWordWrap(True)

        self.gridLayout_2.addWidget(self.energy_tank_capacity_description, 0, 0, 1, 2)


        self.scroll_area_layout.addWidget(self.energy_tank_box)

        self.safe_zone_box = QGroupBox(self.scroll_area_contents)
        self.safe_zone_box.setObjectName(u"safe_zone_box")
        self.gridLayout = QGridLayout(self.safe_zone_box)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setContentsMargins(11, 11, 11, 11)
        self.gridLayout.setObjectName(u"gridLayout")
        self.safe_zone_regen_spin = QDoubleSpinBox(self.safe_zone_box)
        self.safe_zone_regen_spin.setObjectName(u"safe_zone_regen_spin")
        self.safe_zone_regen_spin.setMaximum(100.000000000000000)
        self.safe_zone_regen_spin.setSingleStep(0.100000000000000)
        self.safe_zone_regen_spin.setValue(1.000000000000000)

        self.gridLayout.addWidget(self.safe_zone_regen_spin, 2, 1, 1, 1)

        self.safe_zone_regen_label = QLabel(self.safe_zone_box)
        self.safe_zone_regen_label.setObjectName(u"safe_zone_regen_label")

        self.gridLayout.addWidget(self.safe_zone_regen_label, 2, 0, 1, 1)

        self.safe_zone_logic_heal_check = QCheckBox(self.safe_zone_box)
        self.safe_zone_logic_heal_check.setObjectName(u"safe_zone_logic_heal_check")
        self.safe_zone_logic_heal_check.setEnabled(False)
        self.safe_zone_logic_heal_check.setChecked(True)

        self.gridLayout.addWidget(self.safe_zone_logic_heal_check, 1, 0, 1, 2)

        self.safe_zone_description = QLabel(self.safe_zone_box)
        self.safe_zone_description.setObjectName(u"safe_zone_description")
        self.safe_zone_description.setWordWrap(True)

        self.gridLayout.addWidget(self.safe_zone_description, 0, 0, 1, 2)


        self.scroll_area_layout.addWidget(self.safe_zone_box)

        self.dark_aether_box = QGroupBox(self.scroll_area_contents)
        self.dark_aether_box.setObjectName(u"dark_aether_box")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.dark_aether_box.sizePolicy().hasHeightForWidth())
        self.dark_aether_box.setSizePolicy(sizePolicy1)
        self.dark_aether_layout_2 = QGridLayout(self.dark_aether_box)
        self.dark_aether_layout_2.setSpacing(6)
        self.dark_aether_layout_2.setContentsMargins(11, 11, 11, 11)
        self.dark_aether_layout_2.setObjectName(u"dark_aether_layout_2")
        self.varia_suit_spin_box = QDoubleSpinBox(self.dark_aether_box)
        self.varia_suit_spin_box.setObjectName(u"varia_suit_spin_box")
        self.varia_suit_spin_box.setMaximum(60.000000000000000)
        self.varia_suit_spin_box.setStepType(QAbstractSpinBox.AdaptiveDecimalStepType)
        self.varia_suit_spin_box.setValue(6.000000000000000)

        self.dark_aether_layout_2.addWidget(self.varia_suit_spin_box, 2, 1, 1, 1)

        self.varia_suit_label = QLabel(self.dark_aether_box)
        self.varia_suit_label.setObjectName(u"varia_suit_label")

        self.dark_aether_layout_2.addWidget(self.varia_suit_label, 2, 0, 1, 1)

        self.dark_suit_label = QLabel(self.dark_aether_box)
        self.dark_suit_label.setObjectName(u"dark_suit_label")

        self.dark_aether_layout_2.addWidget(self.dark_suit_label, 3, 0, 1, 1)

        self.dark_suit_spin_box = QDoubleSpinBox(self.dark_aether_box)
        self.dark_suit_spin_box.setObjectName(u"dark_suit_spin_box")
        self.dark_suit_spin_box.setMaximum(60.000000000000000)
        self.dark_suit_spin_box.setStepType(QAbstractSpinBox.AdaptiveDecimalStepType)
        self.dark_suit_spin_box.setValue(1.200000000000000)

        self.dark_aether_layout_2.addWidget(self.dark_suit_spin_box, 3, 1, 1, 1)

        self.dark_aether_label = QLabel(self.dark_aether_box)
        self.dark_aether_label.setObjectName(u"dark_aether_label")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.dark_aether_label.sizePolicy().hasHeightForWidth())
        self.dark_aether_label.setSizePolicy(sizePolicy2)
        self.dark_aether_label.setWordWrap(True)

        self.dark_aether_layout_2.addWidget(self.dark_aether_label, 0, 0, 1, 2)

        self.dark_aether_box_spacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.dark_aether_layout_2.addItem(self.dark_aether_box_spacer, 1, 0, 1, 2)


        self.scroll_area_layout.addWidget(self.dark_aether_box)

        self.energy_tank_spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.scroll_area_layout.addItem(self.energy_tank_spacer)

        self.scroll_area.setWidget(self.scroll_area_contents)

        self.main_layout.addWidget(self.scroll_area)

        PresetEchoesEnergy.setCentralWidget(self.centralWidget)

        self.retranslateUi(PresetEchoesEnergy)

        QMetaObject.connectSlotsByName(PresetEchoesEnergy)
    # setupUi

    def retranslateUi(self, PresetEchoesEnergy):
        PresetEchoesEnergy.setWindowTitle(QCoreApplication.translate("PresetEchoesEnergy", u"Energy", None))
        self.energy_tank_box.setTitle(QCoreApplication.translate("PresetEchoesEnergy", u"Energy tank", None))
        self.energy_tank_capacity_label.setText(QCoreApplication.translate("PresetEchoesEnergy", u"Energy per tank", None))
        self.energy_tank_capacity_spin_box.setSuffix(QCoreApplication.translate("PresetEchoesEnergy", u" energy", None))
        self.dangerous_tank_check.setText(QCoreApplication.translate("PresetEchoesEnergy", u"1 HP mode. In this mode, Energy Tanks and Save Stations leave you at 1 HP instead", None))
        self.energy_tank_capacity_description.setText(QCoreApplication.translate("PresetEchoesEnergy", u"<html><head/><body><p>Configure how much energy each Energy Tank you collect will provide. Your base energy is always this quantity, minus 1.</p><p>While logic will respect this value, only the original value (100) has been tested.</p></body></html>", None))
        self.safe_zone_box.setTitle(QCoreApplication.translate("PresetEchoesEnergy", u"Safe zone", None))
        self.safe_zone_regen_spin.setSuffix(QCoreApplication.translate("PresetEchoesEnergy", u" energy/s", None))
        self.safe_zone_regen_label.setText(QCoreApplication.translate("PresetEchoesEnergy", u"Safe Zone healing rate", None))
        self.safe_zone_logic_heal_check.setText(QCoreApplication.translate("PresetEchoesEnergy", u"Logic considers fully healing at every safe zone. This is currently always on.", None))
        self.safe_zone_description.setText(QCoreApplication.translate("PresetEchoesEnergy", u"<html><head/><body><p>Configure how Dark Aether safe zones operate and how logic uses them.</p></body></html>", None))
        self.dark_aether_box.setTitle(QCoreApplication.translate("PresetEchoesEnergy", u"Dark Aether", None))
        self.varia_suit_spin_box.setSuffix(QCoreApplication.translate("PresetEchoesEnergy", u" energy/s", None))
        self.varia_suit_label.setText(QCoreApplication.translate("PresetEchoesEnergy", u"Varia Suit", None))
        self.dark_suit_label.setText(QCoreApplication.translate("PresetEchoesEnergy", u"Dark Suit", None))
        self.dark_suit_spin_box.setSuffix(QCoreApplication.translate("PresetEchoesEnergy", u" energy/s", None))
        self.dark_aether_label.setText(QCoreApplication.translate("PresetEchoesEnergy", u"<html><head/><body><p>Configure how much damage per second you take in Dark Aether, per suit.<br/>Light Suit is always immune.</p></body></html>", None))
    # retranslateUi

