# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_prime_hints.ui'
##
## Created by: Qt User Interface Compiler version 6.7.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import *  # type: ignore
from PySide6.QtGui import *  # type: ignore
from PySide6.QtWidgets import *  # type: ignore

class Ui_PresetPrimeHints(object):
    def setupUi(self, PresetPrimeHints):
        if not PresetPrimeHints.objectName():
            PresetPrimeHints.setObjectName(u"PresetPrimeHints")
        PresetPrimeHints.resize(423, 259)
        self.centralWidget = QWidget(PresetPrimeHints)
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

        self.phazon_suit_hint_group = QGroupBox(self.centralWidget)
        self.phazon_suit_hint_group.setObjectName(u"phazon_suit_hint_group")
        self.verticalLayout_10 = QVBoxLayout(self.phazon_suit_hint_group)
        self.verticalLayout_10.setSpacing(6)
        self.verticalLayout_10.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")
        self.verticalLayout_10.setContentsMargins(9, 9, 9, 9)
        self.phazon_suit_hint_label = QLabel(self.phazon_suit_hint_group)
        self.phazon_suit_hint_label.setObjectName(u"phazon_suit_hint_label")
        self.phazon_suit_hint_label.setWordWrap(True)

        self.verticalLayout_10.addWidget(self.phazon_suit_hint_label)

        self.phazon_suit_hint_combo = QComboBox(self.phazon_suit_hint_group)
        self.phazon_suit_hint_combo.addItem("")
        self.phazon_suit_hint_combo.addItem("")
        self.phazon_suit_hint_combo.addItem("")
        self.phazon_suit_hint_combo.setObjectName(u"phazon_suit_hint_combo")

        self.verticalLayout_10.addWidget(self.phazon_suit_hint_combo)


        self.hint_layout.addWidget(self.phazon_suit_hint_group)

        PresetPrimeHints.setCentralWidget(self.centralWidget)

        self.retranslateUi(PresetPrimeHints)

        QMetaObject.connectSlotsByName(PresetPrimeHints)
    # setupUi

    def retranslateUi(self, PresetPrimeHints):
        PresetPrimeHints.setWindowTitle(QCoreApplication.translate("PresetPrimeHints", u"Hints", None))
        self.hint_artifact_group.setTitle(QCoreApplication.translate("PresetPrimeHints", u"Artifacts", None))
        self.hint_artifact_label.setText(QCoreApplication.translate("PresetPrimeHints", u"<html><head/><body><p>This controls how precise the hints for Chozo Artifacts in Artifact Temple are.</p><p><span style=\" font-weight:600;\">No hints</span>: The scans provide no useful information.</p><p><span style=\" font-weight:600;\">Show only the area name</span>: Each scan says the corresponding artifact is in &quot;Tallon Overworld&quot;, &quot;Chozo Ruins&quot;, etc.</p><p><span style=\" font-weight:600;\">Show area and room name</span>: Each scan says the corresponding artifact is in &quot;Tallon Overworld - Transport Tunnel B&quot;, &quot;Phazon Mines - Metroid Quarantine B&quot;, etc. For rooms with more than one item location, there's no way to distinguish which one of them that artifact is in.</p></body></html>", None))
        self.hint_artifact_combo.setItemText(0, QCoreApplication.translate("PresetPrimeHints", u"No hints", None))
        self.hint_artifact_combo.setItemText(1, QCoreApplication.translate("PresetPrimeHints", u"Show only the area name", None))
        self.hint_artifact_combo.setItemText(2, QCoreApplication.translate("PresetPrimeHints", u"Show area and room name", None))

        self.phazon_suit_hint_group.setTitle(QCoreApplication.translate("PresetPrimeHints", u"Phazon Suit", None))
        self.phazon_suit_hint_label.setText(QCoreApplication.translate("PresetPrimeHints", u"<html><head/><body><p>This controls how precise the hint for Phazon Suit in Impact Crater is.</p><p><span style=\" font-weight:600;\">No hint</span>: No hint is added.</p><p><span style=\" font-weight:600;\">Show only the area name</span>: A scan post will be placed in Crater Entry Point revealing Phazon Suit's area (e.g. Player 2's Phazon Mines).</p><p><span style=\" font-weight:600;\">Show area and room name</span>: Same as above, but shows the exact room name.</p></body></html>", None))
        self.phazon_suit_hint_combo.setItemText(0, QCoreApplication.translate("PresetPrimeHints", u"No hint", None))
        self.phazon_suit_hint_combo.setItemText(1, QCoreApplication.translate("PresetPrimeHints", u"Show only the area name", None))
        self.phazon_suit_hint_combo.setItemText(2, QCoreApplication.translate("PresetPrimeHints", u"Show area and room name", None))

    # retranslateUi

