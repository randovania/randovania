# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_am2r_hints.ui'
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
    QMainWindow, QScrollArea, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

class Ui_PresetAM2RHints(object):
    def setupUi(self, PresetAM2RHints):
        if not PresetAM2RHints.objectName():
            PresetAM2RHints.setObjectName(u"PresetAM2RHints")
        PresetAM2RHints.resize(699, 570)
        self.centralWidget = QWidget(PresetAM2RHints)
        self.centralWidget.setObjectName(u"centralWidget")
        self.centralWidget.setMaximumSize(QSize(16777215, 16777215))
        self.hint_layout = QVBoxLayout(self.centralWidget)
        self.hint_layout.setSpacing(6)
        self.hint_layout.setContentsMargins(11, 11, 11, 11)
        self.hint_layout.setObjectName(u"hint_layout")
        self.hint_layout.setContentsMargins(6, 6, 6, 6)
        self.scroll_area = QScrollArea(self.centralWidget)
        self.scroll_area.setObjectName(u"scroll_area")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area_contents = QWidget()
        self.scroll_area_contents.setObjectName(u"scroll_area_contents")
        self.scroll_area_contents.setGeometry(QRect(0, 0, 687, 558))
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
        self.hint_artifact_group = QGroupBox(self.scroll_area_contents)
        self.hint_artifact_group.setObjectName(u"hint_artifact_group")
        self.verticalLayout_9 = QVBoxLayout(self.hint_artifact_group)
        self.verticalLayout_9.setSpacing(6)
        self.verticalLayout_9.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.verticalLayout_9.setContentsMargins(6, 6, 6, 6)
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


        self.scroll_area_layout.addWidget(self.hint_artifact_group)

        self.ice_beam_hint_group = QGroupBox(self.scroll_area_contents)
        self.ice_beam_hint_group.setObjectName(u"ice_beam_hint_group")
        self.verticalLayout = QVBoxLayout(self.ice_beam_hint_group)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(6, 6, 6, 6)
        self.ice_beam_hint_label = QLabel(self.ice_beam_hint_group)
        self.ice_beam_hint_label.setObjectName(u"ice_beam_hint_label")
        self.ice_beam_hint_label.setWordWrap(True)

        self.verticalLayout.addWidget(self.ice_beam_hint_label)

        self.ice_beam_hint_combo = QComboBox(self.ice_beam_hint_group)
        self.ice_beam_hint_combo.addItem("")
        self.ice_beam_hint_combo.addItem("")
        self.ice_beam_hint_combo.addItem("")
        self.ice_beam_hint_combo.setObjectName(u"ice_beam_hint_combo")

        self.verticalLayout.addWidget(self.ice_beam_hint_combo)


        self.scroll_area_layout.addWidget(self.ice_beam_hint_group)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.scroll_area_layout.addItem(self.verticalSpacer_2)

        self.scroll_area.setWidget(self.scroll_area_contents)

        self.hint_layout.addWidget(self.scroll_area)

        PresetAM2RHints.setCentralWidget(self.centralWidget)

        self.retranslateUi(PresetAM2RHints)

        QMetaObject.connectSlotsByName(PresetAM2RHints)
    # setupUi

    def retranslateUi(self, PresetAM2RHints):
        PresetAM2RHints.setWindowTitle(QCoreApplication.translate("PresetAM2RHints", u"Hints", None))
        self.hint_artifact_group.setTitle(QCoreApplication.translate("PresetAM2RHints", u"DNA", None))
        self.hint_artifact_label.setText(QCoreApplication.translate("PresetAM2RHints", u"<html><head/><body><p>This controls\n"
"                                                        how precise the DNA hints for the Wisdom Septoggs are.</p><p><span\n"
"                                                        style=\" font-weight:600;\">No hints</span>:\n"
"                                                        The hints provide no useful information.</p><p><span\n"
"                                                        style=\" font-weight:600;\">Show only the area name</span>:\n"
"                                                        Each hint says the area name for the corresponding DNA (&quot;Golden\n"
"                                                        Temple&quot;, &quot;Hydro Station&quot;, etc.)</p><p><span\n"
"                                                        style=\" font-weight:600;\">Show area and room name</span>:\n"
"                                                        Each scan says the area and room name for the corresponding DNA\n"
"                            "
                        "                            (&quot;Golden Temple - Exterior Alpha Nest&quot;, &quot;The\n"
"                                                        Nest - Hideout Alpha Nest&quot;, etc.). For rooms with more\n"
"                                                        than one item location, there's no way to distinguish which one\n"
"                                                        of them contains the DNA.</p></body></html>\n"
"                                                    ", None))
        self.hint_artifact_combo.setItemText(0, QCoreApplication.translate("PresetAM2RHints", u"No hints", None))
        self.hint_artifact_combo.setItemText(1, QCoreApplication.translate("PresetAM2RHints", u"Show only the area name", None))
        self.hint_artifact_combo.setItemText(2, QCoreApplication.translate("PresetAM2RHints", u"Show area and room name", None))

        self.ice_beam_hint_group.setTitle(QCoreApplication.translate("PresetAM2RHints", u"Ice Beam", None))
        self.ice_beam_hint_label.setText(QCoreApplication.translate("PresetAM2RHints", u"<html><head/><body><p>This controls\n"
"                                                        how precise the hint for Ice Beam in Genetics Laboratory is.</p><p><span\n"
"                                                        style=\" font-weight:600;\">No hint</span>: No\n"
"                                                        hint is added.</p><p><span style=\"\n"
"                                                        font-weight:600;\">Show only the area name</span>:\n"
"                                                        The Chozo scan will be replaced with a hint revealing Ice Beam's\n"
"                                                        area (e.g. Player 2's GFS Thoth).</p><p><span\n"
"                                                        style=\" font-weight:600;\">Show area and room name</span>:\n"
"                                                        Same as above, but also shows the exact room name.</p></body></html>\n"
"                                                    ", None))
        self.ice_beam_hint_combo.setItemText(0, QCoreApplication.translate("PresetAM2RHints", u"No hint", None))
        self.ice_beam_hint_combo.setItemText(1, QCoreApplication.translate("PresetAM2RHints", u"Show only the area name", None))
        self.ice_beam_hint_combo.setItemText(2, QCoreApplication.translate("PresetAM2RHints", u"Show area and room name", None))

    # retranslateUi

