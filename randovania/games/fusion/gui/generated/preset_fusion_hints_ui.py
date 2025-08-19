# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_fusion_hints.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QGroupBox, QLabel,
    QMainWindow, QScrollArea, QSizePolicy, QVBoxLayout,
    QWidget)

class Ui_PresetFusionHints(object):
    def setupUi(self, PresetFusionHints):
        if not PresetFusionHints.objectName():
            PresetFusionHints.setObjectName(u"PresetFusionHints")
        PresetFusionHints.resize(574, 461)
        self.centralWidget = QWidget(PresetFusionHints)
        self.centralWidget.setObjectName(u"centralWidget")
        self.centralWidget.setMaximumSize(QSize(16777215, 16777215))
        self.hint_layout = QVBoxLayout(self.centralWidget)
        self.hint_layout.setSpacing(6)
        self.hint_layout.setContentsMargins(11, 11, 11, 11)
        self.hint_layout.setObjectName(u"hint_layout")
        self.hint_layout.setContentsMargins(4, 8, 4, 0)
        self.scrollArea = QScrollArea(self.centralWidget)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 564, 451))
        self.verticalLayout = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.hint_artifact_group = QGroupBox(self.scrollAreaWidgetContents)
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


        self.verticalLayout.addWidget(self.hint_artifact_group)

        self.charge_beam_hint_group = QGroupBox(self.scrollAreaWidgetContents)
        self.charge_beam_hint_group.setObjectName(u"charge_beam_hint_group")
        self.verticalLayout_10 = QVBoxLayout(self.charge_beam_hint_group)
        self.verticalLayout_10.setSpacing(6)
        self.verticalLayout_10.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")
        self.verticalLayout_10.setContentsMargins(9, 9, 9, 9)
        self.charge_beam_hint_label = QLabel(self.charge_beam_hint_group)
        self.charge_beam_hint_label.setObjectName(u"charge_beam_hint_label")
        self.charge_beam_hint_label.setWordWrap(True)

        self.verticalLayout_10.addWidget(self.charge_beam_hint_label)

        self.charge_beam_hint_combo = QComboBox(self.charge_beam_hint_group)
        self.charge_beam_hint_combo.addItem("")
        self.charge_beam_hint_combo.addItem("")
        self.charge_beam_hint_combo.addItem("")
        self.charge_beam_hint_combo.setObjectName(u"charge_beam_hint_combo")

        self.verticalLayout_10.addWidget(self.charge_beam_hint_combo)


        self.verticalLayout.addWidget(self.charge_beam_hint_group)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.hint_layout.addWidget(self.scrollArea)

        PresetFusionHints.setCentralWidget(self.centralWidget)

        self.retranslateUi(PresetFusionHints)

        QMetaObject.connectSlotsByName(PresetFusionHints)
    # setupUi

    def retranslateUi(self, PresetFusionHints):
        PresetFusionHints.setWindowTitle(QCoreApplication.translate("PresetFusionHints", u"Hints", None))
        self.hint_artifact_group.setTitle(QCoreApplication.translate("PresetFusionHints", u"Infant Metroids", None))
        self.hint_artifact_label.setText(QCoreApplication.translate("PresetFusionHints", u"<html><head/><body><p>This controls how precise the Infant Metroids hint at Restricted Labs is.</p><p><span style=\" font-weight:600;\">No hints</span>: The hints provide no useful information.</p><p><span style=\" font-weight:600;\">Show only the area name</span>: The hint will say the area name for the corresponding Metroid (&quot;Main Deck&quot;, &quot;Sector 1 (SRX)&quot;, etc.)</p><p><span style=\" font-weight:600;\">Show area and room name</span>: The hint says the area and room name for the corresponding Metroid (&quot;Main Deck - Arachnus Arena&quot;, &quot;Sector 1 (SRX) - Hornoad Hole&quot;, etc.). For rooms with more than one item location, there's no way to distinguish which one of them contains the Metroid.</p></body></html>", None))
        self.hint_artifact_combo.setItemText(0, QCoreApplication.translate("PresetFusionHints", u"No hints", None))
        self.hint_artifact_combo.setItemText(1, QCoreApplication.translate("PresetFusionHints", u"Show only the area name", None))
        self.hint_artifact_combo.setItemText(2, QCoreApplication.translate("PresetFusionHints", u"Show area and room name", None))

        self.charge_beam_hint_group.setTitle(QCoreApplication.translate("PresetFusionHints", u"Charge Beam", None))
        self.charge_beam_hint_label.setText(QCoreApplication.translate("PresetFusionHints", u"<html><head/><body><p>This controls how precise the hint for Charge Beam in Auxiliary Navigation Room is.</p><p><span style=\" font-weight:600;\">No hint</span>: No hint is added.</p><p><span style=\" font-weight:600;\">Show only the area name</span>: The Navigation Terminal will be replaced with a hint revealing Charge Beam's area (e.g. Player 2's Chozo Ruins).</p><p><span style=\" font-weight:600;\">Show area and room name</span>: Same as above, but also shows the exact room name.</p></body></html>", None))
        self.charge_beam_hint_combo.setItemText(0, QCoreApplication.translate("PresetFusionHints", u"No hint", None))
        self.charge_beam_hint_combo.setItemText(1, QCoreApplication.translate("PresetFusionHints", u"Show only the area name", None))
        self.charge_beam_hint_combo.setItemText(2, QCoreApplication.translate("PresetFusionHints", u"Show area and room name", None))

    # retranslateUi

