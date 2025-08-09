# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_msr_hints.ui'
##
## Created by: Qt User Interface Compiler version 6.6.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import *  # type: ignore
from PySide6.QtGui import *  # type: ignore
from PySide6.QtWidgets import *  # type: ignore

class Ui_PresetMSRHints(object):
    def setupUi(self, PresetMSRHints):
        if not PresetMSRHints.objectName():
            PresetMSRHints.setObjectName(u"PresetMSRHints")
        PresetMSRHints.resize(423, 437)
        self.centralWidget = QWidget(PresetMSRHints)
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

        PresetMSRHints.setCentralWidget(self.centralWidget)

        self.retranslateUi(PresetMSRHints)

        QMetaObject.connectSlotsByName(PresetMSRHints)
    # setupUi

    def retranslateUi(self, PresetMSRHints):
        PresetMSRHints.setWindowTitle(QCoreApplication.translate("PresetMSRHints", u"Hints", None))
        self.hint_artifact_group.setTitle(QCoreApplication.translate("PresetMSRHints", u"Metroid DNA", None))
        self.hint_artifact_label.setText(QCoreApplication.translate("PresetMSRHints", u"<html><head/><body><p>This controls how precise the Metroid DNA hints for the DNA Chozo Seals are.</p><p><span style=\" font-weight:600;\">No hints</span>: The hints provide no useful information.</p><p><span style=\" font-weight:600;\">Show only the area name</span>: Each hint says the area name for the corresponding Metroid DNA (&quot;Area 1&quot;, &quot;Area 6&quot;, etc.)</p><p><span style=\" font-weight:600;\">Show area and room name</span>: Each scan says the area and room name for the corresponding Metroid DNA (&quot;Area 1 - Exterior Alpha Arena&quot;, &quot;Area 6 - Zeta Arena&quot;, etc.). For rooms with more than one item location, there's no way to distinguish which one of them contains the Metroid DNA.</p></body></html>", None))
        self.hint_artifact_combo.setItemText(0, QCoreApplication.translate("PresetMSRHints", u"No hints", None))
        self.hint_artifact_combo.setItemText(1, QCoreApplication.translate("PresetMSRHints", u"Show only the area name", None))
        self.hint_artifact_combo.setItemText(2, QCoreApplication.translate("PresetMSRHints", u"Show area and room name", None))

    # retranslateUi

