# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_msr_aeion.ui'
##
## Created by: Qt User Interface Compiler version 6.6.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import *  # type: ignore
from PySide6.QtGui import *  # type: ignore
from PySide6.QtWidgets import *  # type: ignore

class Ui_PresetMSRAeion(object):
    def setupUi(self, PresetMSRAeion):
        if not PresetMSRAeion.objectName():
            PresetMSRAeion.setObjectName(u"PresetMSRAeion")
        PresetMSRAeion.resize(514, 434)
        self.centralWidget = QWidget(PresetMSRAeion)
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
        self.groupBox = QGroupBox(self.scroll_area_contents)
        self.groupBox.setObjectName(u"groupBox")
        self.gridLayout = QGridLayout(self.groupBox)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setContentsMargins(11, 11, 11, 11)
        self.gridLayout.setObjectName(u"gridLayout")
        self.aeion_capacity_description = QLabel(self.groupBox)
        self.aeion_capacity_description.setObjectName(u"aeion_capacity_description")
        self.aeion_capacity_description.setWordWrap(True)

        self.gridLayout.addWidget(self.aeion_capacity_description, 0, 0, 1, 1)

        self.aeion_capacity_label = QLabel(self.groupBox)
        self.aeion_capacity_label.setObjectName(u"aeion_capacity_label")

        self.gridLayout.addWidget(self.aeion_capacity_label, 4, 0, 1, 1)

        self.aeion_capacity_spin_box = QSpinBox(self.groupBox)
        self.aeion_capacity_spin_box.setObjectName(u"aeion_capacity_spin_box")
        self.aeion_capacity_spin_box.setMinimum(1000)
        self.aeion_capacity_spin_box.setMaximum(2200)
        self.aeion_capacity_spin_box.setSingleStep(10)

        self.gridLayout.addWidget(self.aeion_capacity_spin_box, 4, 1, 1, 1)

        self.aeion_capacity_spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout.addItem(self.aeion_capacity_spacer, 1, 0, 1, 2)


        self.scroll_area_layout.addWidget(self.groupBox)

        self.aeion_tank_spacer = QSpacerItem(17, 314, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.scroll_area_layout.addItem(self.aeion_tank_spacer)

        self.scroll_area.setWidget(self.scroll_area_contents)

        self.main_layout.addWidget(self.scroll_area)

        PresetMSRAeion.setCentralWidget(self.centralWidget)

        self.retranslateUi(PresetMSRAeion)

        QMetaObject.connectSlotsByName(PresetMSRAeion)
    # setupUi

    def retranslateUi(self, PresetMSRAeion):
        PresetMSRAeion.setWindowTitle(QCoreApplication.translate("PresetMSRAeion", u"Energy", None))
        self.groupBox.setTitle(QCoreApplication.translate("PresetMSRAeion", u"Aeion", None))
        self.aeion_capacity_description.setText(QCoreApplication.translate("PresetMSRAeion", u"<html><head/><body><p>Configure your starting aeion.</p></body></html>", None))
        self.aeion_capacity_label.setText(QCoreApplication.translate("PresetMSRAeion", u"Starting Aeion", None))
        self.aeion_capacity_spin_box.setSuffix(QCoreApplication.translate("PresetMSRAeion", u" aeion", None))
    # retranslateUi

