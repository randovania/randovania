# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_cs_objective.ui'
##
## Created by: Qt User Interface Compiler version 6.6.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import *  # type: ignore
from PySide6.QtGui import *  # type: ignore
from PySide6.QtWidgets import *  # type: ignore

class Ui_PresetCSObjective(object):
    def setupUi(self, PresetCSObjective):
        if not PresetCSObjective.objectName():
            PresetCSObjective.setObjectName(u"PresetCSObjective")
        PresetCSObjective.resize(562, 459)
        self.centralWidget = QWidget(PresetCSObjective)
        self.centralWidget.setObjectName(u"centralWidget")
        self.centralWidget.setMaximumSize(QSize(16777215, 16777215))
        self.goal_layout = QVBoxLayout(self.centralWidget)
        self.goal_layout.setSpacing(6)
        self.goal_layout.setContentsMargins(11, 11, 11, 11)
        self.goal_layout.setObjectName(u"goal_layout")
        self.goal_layout.setContentsMargins(4, 8, 4, 8)
        self.goal_description = QLabel(self.centralWidget)
        self.goal_description.setObjectName(u"goal_description")
        self.goal_description.setWordWrap(True)

        self.goal_layout.addWidget(self.goal_description)

        self.goal_combo = QComboBox(self.centralWidget)
        self.goal_combo.addItem("")
        self.goal_combo.addItem("")
        self.goal_combo.addItem("")
        self.goal_combo.addItem("")
        self.goal_combo.setObjectName(u"goal_combo")
        self.goal_combo.setEditable(False)

        self.goal_layout.addWidget(self.goal_combo)

        self.b2_check = QCheckBox(self.centralWidget)
        self.b2_check.setObjectName(u"b2_check")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.b2_check.sizePolicy().hasHeightForWidth())
        self.b2_check.setSizePolicy(sizePolicy)
        self.b2_check.setMinimumSize(QSize(0, 45))

        self.goal_layout.addWidget(self.b2_check)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.goal_layout.addItem(self.horizontalSpacer)

        PresetCSObjective.setCentralWidget(self.centralWidget)

        self.retranslateUi(PresetCSObjective)

        QMetaObject.connectSlotsByName(PresetCSObjective)
    # setupUi

    def retranslateUi(self, PresetCSObjective):
        PresetCSObjective.setWindowTitle(QCoreApplication.translate("PresetCSObjective", u"Objective", None))
        self.goal_description.setText(QCoreApplication.translate("PresetCSObjective", u"<html><head/><body><p>Controls the requirements needed to complete the game.</p><ul style=\"margin-top: 0px; margin-bottom: 0px; margin-left: 0px; margin-right: 0px; -qt-list-indent: 1;\"><li style=\" margin-top:12px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">Bad Ending</span>: Collect the Charcoal, Gum Base, and Jellyfish Juice for MALCO to build the Bomb, and destroy the Core to leave the island with Kazuma.</li><li style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">Normal Ending</span>: Collect the ID Card and save Sue in the Egg Corridor to enter the Throne Room and defeat the Undead Core.</li><li style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">Best Ending</span>: Collect the Booster 2.0 and Iron Bond, and complete the No"
                        "rmal Ending requirements to enter the Throne Room and eventually defeat Ballos.</li><li style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">All Bosses</span>: Complete the Best Ending requirements and defeat every other boss in the game before entering the Throne Room and eventually defeat Ballos.</li><li style=\" margin-top:0px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">100%</span>: Complete the All Bosses requirements and collect every item location in the game before entering the Throne Room and eventually defeat Ballos.</li></ul><p><br/></p></body></html>", None))
        self.goal_combo.setItemText(0, QCoreApplication.translate("PresetCSObjective", u"Bad Ending", None))
        self.goal_combo.setItemText(1, QCoreApplication.translate("PresetCSObjective", u"Normal Ending", None))
        self.goal_combo.setItemText(2, QCoreApplication.translate("PresetCSObjective", u"Best Ending", None))
        self.goal_combo.setItemText(3, QCoreApplication.translate("PresetCSObjective", u"All Bosses", None))

        self.goal_combo.setCurrentText(QCoreApplication.translate("PresetCSObjective", u"Bad Ending", None))
        self.goal_combo.setPlaceholderText("")
        self.b2_check.setText(QCoreApplication.translate("PresetCSObjective", u"Remove falling blocks in B2", None))
    # retranslateUi

