# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_planets_zebeth_hints.ui'
##
## Created by: Qt User Interface Compiler version 6.7.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import *  # type: ignore
from PySide6.QtGui import *  # type: ignore
from PySide6.QtWidgets import *  # type: ignore

class Ui_PresetPlanetsZebethHints(object):
    def setupUi(self, PresetPlanetsZebethHints):
        if not PresetPlanetsZebethHints.objectName():
            PresetPlanetsZebethHints.setObjectName(u"PresetPlanetsZebethHints")
        PresetPlanetsZebethHints.resize(423, 287)
        self.centralWidget = QWidget(PresetPlanetsZebethHints)
        self.centralWidget.setObjectName(u"centralWidget")
        self.centralWidget.setMaximumSize(QSize(16777215, 16777215))
        self.hint_layout = QVBoxLayout(self.centralWidget)
        self.hint_layout.setSpacing(6)
        self.hint_layout.setContentsMargins(11, 11, 11, 11)
        self.hint_layout.setObjectName(u"hint_layout")
        self.hint_layout.setContentsMargins(4, 8, 4, 0)
        self.hint_artifact_group = QGroupBox(self.centralWidget)
        self.hint_artifact_group.setObjectName(u"hint_artifact_group")
        self.verticalLayout_9 = QVBoxLayout(self.hint_artifact_group)
        self.verticalLayout_9.setSpacing(6)
        self.verticalLayout_9.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.verticalLayout_9.setContentsMargins(9, 9, 9, 9)
        self.hint_artifact_label = QLabel(self.hint_artifact_group)
        self.hint_artifact_label.setObjectName(u"hint_artifact_label")
        self.hint_artifact_label.setWordWrap(True)

        self.verticalLayout_9.addWidget(self.hint_artifact_label)

        self.hint_artifact_combo = QComboBox(self.hint_artifact_group)
        self.hint_artifact_combo.addItem("")
        self.hint_artifact_combo.addItem("")
        self.hint_artifact_combo.addItem("")
        self.hint_artifact_combo.setObjectName(u"hint_artifact_combo")

        self.verticalLayout_9.addWidget(self.hint_artifact_combo)


        self.hint_layout.addWidget(self.hint_artifact_group)

        PresetPlanetsZebethHints.setCentralWidget(self.centralWidget)

        self.retranslateUi(PresetPlanetsZebethHints)

        QMetaObject.connectSlotsByName(PresetPlanetsZebethHints)
    # setupUi

    def retranslateUi(self, PresetPlanetsZebethHints):
        PresetPlanetsZebethHints.setWindowTitle(QCoreApplication.translate("PresetPlanetsZebethHints", u"Hints", None))
        self.hint_artifact_group.setTitle(QCoreApplication.translate("PresetPlanetsZebethHints", u"Keys", None))
        self.hint_artifact_label.setText(QCoreApplication.translate("PresetPlanetsZebethHints", u"<html><head/><body><p>This controls how precise the Key hints are.</p><p><span style=\" font-weight:600;\">No hints</span>: The hints provide no useful information.</p><p><span style=\" font-weight:600;\">Show only the area name</span>: Each hint says the area name for the corresponding Key (&quot;Brinstar&quot;, &quot;Kraid&quot;, etc.)</p><p><span style=\" font-weight:600;\">Show area and room name</span>: Each scan says the area and room name for the corresponding Key (&quot;Brinstar - Ice Beam room&quot;, &quot;Kraid - Acid fall&quot;, etc.). For rooms with more than one item location, there's no way to distinguish which one of them contains the Key.</p></body></html>", None))
        self.hint_artifact_combo.setItemText(0, QCoreApplication.translate("PresetPlanetsZebethHints", u"No hints", None))
        self.hint_artifact_combo.setItemText(1, QCoreApplication.translate("PresetPlanetsZebethHints", u"Show only the area name", None))
        self.hint_artifact_combo.setItemText(2, QCoreApplication.translate("PresetPlanetsZebethHints", u"Show area and room name", None))

    # retranslateUi

