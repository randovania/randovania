# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_msr_reserves.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QGridLayout, QGroupBox,
    QLabel, QLayout, QMainWindow, QScrollArea,
    QSizePolicy, QSpacerItem, QSpinBox, QVBoxLayout,
    QWidget)

class Ui_PresetMSRReserves(object):
    def setupUi(self, PresetMSRReserves):
        if not PresetMSRReserves.objectName():
            PresetMSRReserves.setObjectName(u"PresetMSRReserves")
        PresetMSRReserves.setEnabled(True)
        PresetMSRReserves.resize(514, 434)
        self.centralWidget = QWidget(PresetMSRReserves)
        self.centralWidget.setObjectName(u"centralWidget")
        self.centralWidget.setMaximumSize(QSize(16777215, 16777215))
        self.verticalLayout_1 = QVBoxLayout(self.centralWidget)
        self.verticalLayout_1.setSpacing(6)
        self.verticalLayout_1.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_1.setObjectName(u"verticalLayout_1")
        self.verticalLayout_1.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.verticalLayout_1.setContentsMargins(0, 0, 0, 0)
        self.scroll_area = QScrollArea(self.centralWidget)
        self.scroll_area.setObjectName(u"scroll_area")
        self.scroll_area.setMinimumSize(QSize(0, 0))
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area_contents = QWidget()
        self.scroll_area_contents.setObjectName(u"scroll_area_contents")
        self.scroll_area_contents.setGeometry(QRect(0, 0, 493, 469))
        self.scroll_area_contents.setMinimumSize(QSize(0, 469))
        self.verticalLayout_2 = QVBoxLayout(self.scroll_area_contents)
        self.verticalLayout_2.setSpacing(6)
        self.verticalLayout_2.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(6, 6, 6, 6)
        self.reserve_tank_description = QLabel(self.scroll_area_contents)
        self.reserve_tank_description.setObjectName(u"reserve_tank_description")
        self.reserve_tank_description.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.reserve_tank_description)

        self.energy_box = QGroupBox(self.scroll_area_contents)
        self.energy_box.setObjectName(u"energy_box")
        self.gridLayout = QGridLayout(self.energy_box)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setContentsMargins(11, 11, 11, 11)
        self.gridLayout.setObjectName(u"gridLayout")
        self.line = QFrame(self.energy_box)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout.addWidget(self.line, 1, 0, 1, 2)

        self.line_2 = QFrame(self.energy_box)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.Shape.HLine)
        self.line_2.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout.addWidget(self.line_2, 3, 0, 1, 2)

        self.energy_capacity_label = QLabel(self.energy_box)
        self.energy_capacity_label.setObjectName(u"energy_capacity_label")

        self.gridLayout.addWidget(self.energy_capacity_label, 0, 0, 1, 1)

        self.aeion_capacity_label = QLabel(self.energy_box)
        self.aeion_capacity_label.setObjectName(u"aeion_capacity_label")

        self.gridLayout.addWidget(self.aeion_capacity_label, 2, 0, 1, 1)

        self.missile_capacity_label = QLabel(self.energy_box)
        self.missile_capacity_label.setObjectName(u"missile_capacity_label")

        self.gridLayout.addWidget(self.missile_capacity_label, 4, 0, 2, 1)

        self.super_missile_capacity_spin_box = QSpinBox(self.energy_box)
        self.super_missile_capacity_spin_box.setObjectName(u"super_missile_capacity_spin_box")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.super_missile_capacity_spin_box.sizePolicy().hasHeightForWidth())
        self.super_missile_capacity_spin_box.setSizePolicy(sizePolicy)
        self.super_missile_capacity_spin_box.setWrapping(True)
        self.super_missile_capacity_spin_box.setFrame(True)
        self.super_missile_capacity_spin_box.setMinimum(1)
        self.super_missile_capacity_spin_box.setMaximum(99)
        self.super_missile_capacity_spin_box.setSingleStep(10)
        self.super_missile_capacity_spin_box.setValue(10)

        self.gridLayout.addWidget(self.super_missile_capacity_spin_box, 5, 1, 1, 1)

        self.missile_capacity_spin_box = QSpinBox(self.energy_box)
        self.missile_capacity_spin_box.setObjectName(u"missile_capacity_spin_box")
        sizePolicy.setHeightForWidth(self.missile_capacity_spin_box.sizePolicy().hasHeightForWidth())
        self.missile_capacity_spin_box.setSizePolicy(sizePolicy)
        self.missile_capacity_spin_box.setWrapping(True)
        self.missile_capacity_spin_box.setMinimum(1)
        self.missile_capacity_spin_box.setMaximum(999)
        self.missile_capacity_spin_box.setSingleStep(10)
        self.missile_capacity_spin_box.setValue(30)

        self.gridLayout.addWidget(self.missile_capacity_spin_box, 4, 1, 1, 1)

        self.aeion_capacity_spin_box = QSpinBox(self.energy_box)
        self.aeion_capacity_spin_box.setObjectName(u"aeion_capacity_spin_box")
        sizePolicy.setHeightForWidth(self.aeion_capacity_spin_box.sizePolicy().hasHeightForWidth())
        self.aeion_capacity_spin_box.setSizePolicy(sizePolicy)
        self.aeion_capacity_spin_box.setWrapping(True)
        self.aeion_capacity_spin_box.setMinimum(1)
        self.aeion_capacity_spin_box.setMaximum(2200)
        self.aeion_capacity_spin_box.setSingleStep(10)
        self.aeion_capacity_spin_box.setValue(500)

        self.gridLayout.addWidget(self.aeion_capacity_spin_box, 2, 1, 1, 1)

        self.energy_capacity_spin_box = QSpinBox(self.energy_box)
        self.energy_capacity_spin_box.setObjectName(u"energy_capacity_spin_box")
        sizePolicy.setHeightForWidth(self.energy_capacity_spin_box.sizePolicy().hasHeightForWidth())
        self.energy_capacity_spin_box.setSizePolicy(sizePolicy)
        self.energy_capacity_spin_box.setWrapping(True)
        self.energy_capacity_spin_box.setMinimum(1)
        self.energy_capacity_spin_box.setMaximum(1099)
        self.energy_capacity_spin_box.setSingleStep(10)
        self.energy_capacity_spin_box.setValue(299)

        self.gridLayout.addWidget(self.energy_capacity_spin_box, 0, 1, 1, 1)


        self.verticalLayout_2.addWidget(self.energy_box)

        self.reserve_tank_spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.reserve_tank_spacer)

        self.scroll_area.setWidget(self.scroll_area_contents)

        self.verticalLayout_1.addWidget(self.scroll_area)

        PresetMSRReserves.setCentralWidget(self.centralWidget)

        self.retranslateUi(PresetMSRReserves)

        QMetaObject.connectSlotsByName(PresetMSRReserves)
    # setupUi

    def retranslateUi(self, PresetMSRReserves):
        PresetMSRReserves.setWindowTitle(QCoreApplication.translate("PresetMSRReserves", u"Reserves", None))
        self.reserve_tank_description.setText(QCoreApplication.translate("PresetMSRReserves", u"<html><head/><body><p>Reserve Tanks restore a certain amount of Energy/Aeion/Ammo when the respective resource is depleted. To refill a Reserve Tank after it has been used, visit the ship or a respective refill station. Below, you can configure how much each Reserve Tank restores upon activation.</p><p><span style=\" font-weight:600;\">Note</span>: Missile Reserve Tanks restore <span style=\" font-style:italic;\">only </span>one ammo type at a time, not both.</p></body></html>", None))
        self.energy_box.setTitle(QCoreApplication.translate("PresetMSRReserves", u"Configuration", None))
        self.energy_capacity_label.setText(QCoreApplication.translate("PresetMSRReserves", u"Energy Reserve Tank", None))
        self.aeion_capacity_label.setText(QCoreApplication.translate("PresetMSRReserves", u"Aeion Reserve Tank", None))
        self.missile_capacity_label.setText(QCoreApplication.translate("PresetMSRReserves", u"Missile Reserve Tank", None))
        self.super_missile_capacity_spin_box.setSuffix(QCoreApplication.translate("PresetMSRReserves", u" super missiles", None))
        self.missile_capacity_spin_box.setSuffix(QCoreApplication.translate("PresetMSRReserves", u" missiles", None))
        self.aeion_capacity_spin_box.setSuffix(QCoreApplication.translate("PresetMSRReserves", u" aeion", None))
        self.energy_capacity_spin_box.setSuffix(QCoreApplication.translate("PresetMSRReserves", u" energy", None))
    # retranslateUi

