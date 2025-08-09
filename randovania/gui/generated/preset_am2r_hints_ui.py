# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_am2r_hints.ui'
##
## Created by: Qt User Interface Compiler version 6.6.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import *  # type: ignore
from PySide6.QtGui import *  # type: ignore
from PySide6.QtWidgets import *  # type: ignore

class Ui_PresetAM2RHints(object):
    def setupUi(self, PresetAM2RHints):
        if not PresetAM2RHints.objectName():
            PresetAM2RHints.setObjectName(u"PresetAM2RHints")
        PresetAM2RHints.resize(423, 402)
        self.centralWidget = QWidget(PresetAM2RHints)
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

        self.ice_beam_hint_group = QGroupBox(self.centralWidget)
        self.ice_beam_hint_group.setObjectName(u"ice_beam_hint_group")
        self.verticalLayout_10 = QVBoxLayout(self.ice_beam_hint_group)
        self.verticalLayout_10.setSpacing(6)
        self.verticalLayout_10.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")
        self.verticalLayout_10.setContentsMargins(9, 9, 9, 9)
        self.ice_beam_hint_label = QLabel(self.ice_beam_hint_group)
        self.ice_beam_hint_label.setObjectName(u"ice_beam_hint_label")
        self.ice_beam_hint_label.setWordWrap(True)

        self.verticalLayout_10.addWidget(self.ice_beam_hint_label)

        self.ice_beam_hint_combo = QComboBox(self.ice_beam_hint_group)
        self.ice_beam_hint_combo.addItem("")
        self.ice_beam_hint_combo.addItem("")
        self.ice_beam_hint_combo.addItem("")
        self.ice_beam_hint_combo.setObjectName(u"ice_beam_hint_combo")

        self.verticalLayout_10.addWidget(self.ice_beam_hint_combo)


        self.hint_layout.addWidget(self.ice_beam_hint_group)

        PresetAM2RHints.setCentralWidget(self.centralWidget)

        self.retranslateUi(PresetAM2RHints)

        QMetaObject.connectSlotsByName(PresetAM2RHints)
    # setupUi

    def retranslateUi(self, PresetAM2RHints):
        PresetAM2RHints.setWindowTitle(QCoreApplication.translate("PresetAM2RHints", u"Hints", None))
        self.hint_artifact_group.setTitle(QCoreApplication.translate("PresetAM2RHints", u"DNA", None))
        self.hint_artifact_label.setText(QCoreApplication.translate("PresetAM2RHints", u"<html><head/><body><p>This controls how precise the DNA hints for the Wisdom Septoggs are.</p><p><span style=\" font-weight:600;\">No hints</span>: The hints provide no useful information.</p><p><span style=\" font-weight:600;\">Show only the area name</span>: Each hint says the area name for the corresponding DNA (&quot;Golden Temple&quot;, &quot;Hydro Station&quot;, etc.)</p><p><span style=\" font-weight:600;\">Show area and room name</span>: Each scan says the area and room name for the corresponding DNA (&quot;Golden Temple - Exterior Alpha Nest&quot;, &quot;The Nest - Hideout Alpha Nest&quot;, etc.). For rooms with more than one item location, there's no way to distinguish which one of them contains the DNA.</p></body></html>", None))
        self.hint_artifact_combo.setItemText(0, QCoreApplication.translate("PresetAM2RHints", u"No hints", None))
        self.hint_artifact_combo.setItemText(1, QCoreApplication.translate("PresetAM2RHints", u"Show only the area name", None))
        self.hint_artifact_combo.setItemText(2, QCoreApplication.translate("PresetAM2RHints", u"Show area and room name", None))

        self.ice_beam_hint_group.setTitle(QCoreApplication.translate("PresetAM2RHints", u"Ice Beam", None))
        self.ice_beam_hint_label.setText(QCoreApplication.translate("PresetAM2RHints", u"<html><head/><body><p>This controls how precise the hint for Ice Beam in Genetics Laboratory is.</p><p><span style=\" font-weight:600;\">No hint</span>: No hint is added.</p><p><span style=\" font-weight:600;\">Show only the area name</span>: The Chozo scan will be replaced with a hint revealing Ice Beam's area (e.g. Player 2's GFS Thoth).</p><p><span style=\" font-weight:600;\">Show area and room name</span>: Same as above, but also shows the exact room name.</p></body></html>", None))
        self.ice_beam_hint_combo.setItemText(0, QCoreApplication.translate("PresetAM2RHints", u"No hint", None))
        self.ice_beam_hint_combo.setItemText(1, QCoreApplication.translate("PresetAM2RHints", u"Show only the area name", None))
        self.ice_beam_hint_combo.setItemText(2, QCoreApplication.translate("PresetAM2RHints", u"Show area and room name", None))

    # retranslateUi

