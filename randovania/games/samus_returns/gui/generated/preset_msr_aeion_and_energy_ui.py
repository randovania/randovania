# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_msr_aeion_and_energy.ui'
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

class Ui_PresetMSRAeionAndEnergy(object):
    def setupUi(self, PresetMSRAeionAndEnergy):
        if not PresetMSRAeionAndEnergy.objectName():
            PresetMSRAeionAndEnergy.setObjectName(u"PresetMSRAeionAndEnergy")
        PresetMSRAeionAndEnergy.resize(514, 434)
        self.centralWidget = QWidget(PresetMSRAeionAndEnergy)
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
        self.scroll_area_contents.setGeometry(QRect(0, 0, 502, 422))
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
        self.aeion_box = QGroupBox(self.scroll_area_contents)
        self.aeion_box.setObjectName(u"aeion_box")
        self.gridLayout = QGridLayout(self.aeion_box)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setContentsMargins(11, 11, 11, 11)
        self.gridLayout.setObjectName(u"gridLayout")
        self.aeion_capacity_description = QLabel(self.aeion_box)
        self.aeion_capacity_description.setObjectName(u"aeion_capacity_description")
        self.aeion_capacity_description.setWordWrap(True)

        self.gridLayout.addWidget(self.aeion_capacity_description, 0, 0, 1, 1)

        self.aeion_capacity_label = QLabel(self.aeion_box)
        self.aeion_capacity_label.setObjectName(u"aeion_capacity_label")

        self.gridLayout.addWidget(self.aeion_capacity_label, 4, 0, 1, 1)

        self.aeion_capacity_spin_box = QSpinBox(self.aeion_box)
        self.aeion_capacity_spin_box.setObjectName(u"aeion_capacity_spin_box")
        self.aeion_capacity_spin_box.setMinimum(1000)
        self.aeion_capacity_spin_box.setMaximum(2200)
        self.aeion_capacity_spin_box.setSingleStep(10)

        self.gridLayout.addWidget(self.aeion_capacity_spin_box, 4, 1, 1, 1)

        self.aeion_capacity_spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout.addItem(self.aeion_capacity_spacer, 1, 0, 1, 2)


        self.scroll_area_layout.addWidget(self.aeion_box)

        self.constant_environment_damage_box = QGroupBox(self.scroll_area_contents)
        self.constant_environment_damage_box.setObjectName(u"constant_environment_damage_box")
        self.constant_environment_damage_layout = QGridLayout(self.constant_environment_damage_box)
        self.constant_environment_damage_layout.setSpacing(6)
        self.constant_environment_damage_layout.setContentsMargins(11, 11, 11, 11)
        self.constant_environment_damage_layout.setObjectName(u"constant_environment_damage_layout")
        self.constant_heat_damage_check = QCheckBox(self.constant_environment_damage_box)
        self.constant_heat_damage_check.setObjectName(u"constant_heat_damage_check")

        self.constant_environment_damage_layout.addWidget(self.constant_heat_damage_check, 4, 0, 1, 1)

        self.constant_heat_damage_spin_box = QSpinBox(self.constant_environment_damage_box)
        self.constant_heat_damage_spin_box.setObjectName(u"constant_heat_damage_spin_box")
        self.constant_heat_damage_spin_box.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)
        self.constant_heat_damage_spin_box.setMinimum(0)
        self.constant_heat_damage_spin_box.setMaximum(1000)
        self.constant_heat_damage_spin_box.setValue(10)

        self.constant_environment_damage_layout.addWidget(self.constant_heat_damage_spin_box, 4, 1, 1, 1)

        self.constant_lava_damage_check = QCheckBox(self.constant_environment_damage_box)
        self.constant_lava_damage_check.setObjectName(u"constant_lava_damage_check")

        self.constant_environment_damage_layout.addWidget(self.constant_lava_damage_check, 5, 0, 1, 1)

        self.constant_environment_damage_label = QLabel(self.constant_environment_damage_box)
        self.constant_environment_damage_label.setObjectName(u"constant_environment_damage_label")
        self.constant_environment_damage_label.setWordWrap(True)

        self.constant_environment_damage_layout.addWidget(self.constant_environment_damage_label, 6, 0, 1, 2)

        self.constant_lava_damage_spin_box = QSpinBox(self.constant_environment_damage_box)
        self.constant_lava_damage_spin_box.setObjectName(u"constant_lava_damage_spin_box")
        self.constant_lava_damage_spin_box.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)
        self.constant_lava_damage_spin_box.setMinimum(0)
        self.constant_lava_damage_spin_box.setMaximum(1000)
        self.constant_lava_damage_spin_box.setValue(10)

        self.constant_environment_damage_layout.addWidget(self.constant_lava_damage_spin_box, 5, 1, 1, 1)


        self.scroll_area_layout.addWidget(self.constant_environment_damage_box)

        self.spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.scroll_area_layout.addItem(self.spacer)

        self.scroll_area.setWidget(self.scroll_area_contents)

        self.main_layout.addWidget(self.scroll_area)

        PresetMSRAeionAndEnergy.setCentralWidget(self.centralWidget)

        self.retranslateUi(PresetMSRAeionAndEnergy)

        QMetaObject.connectSlotsByName(PresetMSRAeionAndEnergy)
    # setupUi

    def retranslateUi(self, PresetMSRAeionAndEnergy):
        PresetMSRAeionAndEnergy.setWindowTitle(QCoreApplication.translate("PresetMSRAeionAndEnergy", u"Energy", None))
        self.aeion_box.setTitle(QCoreApplication.translate("PresetMSRAeionAndEnergy", u"Aeion", None))
        self.aeion_capacity_description.setText(QCoreApplication.translate("PresetMSRAeionAndEnergy", u"<html><head/><body><p>Configure your starting aeion.</p></body></html>", None))
        self.aeion_capacity_label.setText(QCoreApplication.translate("PresetMSRAeionAndEnergy", u"Starting Aeion", None))
        self.aeion_capacity_spin_box.setSuffix(QCoreApplication.translate("PresetMSRAeionAndEnergy", u" aeion", None))
        self.constant_environment_damage_box.setTitle(QCoreApplication.translate("PresetMSRAeionAndEnergy", u"Environmental Damage", None))
        self.constant_heat_damage_check.setText(QCoreApplication.translate("PresetMSRAeionAndEnergy", u"Use constant heat damage", None))
        self.constant_heat_damage_spin_box.setSuffix(QCoreApplication.translate("PresetMSRAeionAndEnergy", u" damage per second", None))
        self.constant_lava_damage_check.setText(QCoreApplication.translate("PresetMSRAeionAndEnergy", u"Use constant lava damage", None))
        self.constant_environment_damage_label.setText(QCoreApplication.translate("PresetMSRAeionAndEnergy", u"<html><head/><body><p>When enabled, heated rooms or lava will deal a fixed damage per second instead of the normal behavior of scaling up over time.</p><p>Logic will <span style=\" font-weight:696;\">never</span> require heat runs.</p></body></html>", None))
        self.constant_lava_damage_spin_box.setSuffix(QCoreApplication.translate("PresetMSRAeionAndEnergy", u" damage per second", None))
    # retranslateUi

