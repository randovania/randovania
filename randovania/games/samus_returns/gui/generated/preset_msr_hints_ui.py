# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_msr_hints.ui'
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

class Ui_PresetMSRHints(object):
    def setupUi(self, PresetMSRHints):
        if not PresetMSRHints.objectName():
            PresetMSRHints.setObjectName(u"PresetMSRHints")
        PresetMSRHints.resize(595, 580)
        self.centralWidget = QWidget(PresetMSRHints)
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
        self.scroll_area_contents.setGeometry(QRect(0, 0, 581, 566))
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
        self.verticalLayout_2 = QVBoxLayout(self.hint_artifact_group)
        self.verticalLayout_2.setSpacing(6)
        self.verticalLayout_2.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.hint_artifact_label = QLabel(self.hint_artifact_group)
        self.hint_artifact_label.setObjectName(u"hint_artifact_label")
        self.hint_artifact_label.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.hint_artifact_label)

        self.hint_artifact_combo = QComboBox(self.hint_artifact_group)
        self.hint_artifact_combo.addItem("")
        self.hint_artifact_combo.addItem("")
        self.hint_artifact_combo.addItem("")
        self.hint_artifact_combo.setObjectName(u"hint_artifact_combo")

        self.verticalLayout_2.addWidget(self.hint_artifact_combo)


        self.scroll_area_layout.addWidget(self.hint_artifact_group)

        self.hint_fbi_group = QGroupBox(self.scroll_area_contents)
        self.hint_fbi_group.setObjectName(u"hint_fbi_group")
        self.verticalLayout = QVBoxLayout(self.hint_fbi_group)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.hint_fbi_label = QLabel(self.hint_fbi_group)
        self.hint_fbi_label.setObjectName(u"hint_fbi_label")
        self.hint_fbi_label.setWordWrap(True)

        self.verticalLayout.addWidget(self.hint_fbi_label)

        self.hint_fbi_combo = QComboBox(self.hint_fbi_group)
        self.hint_fbi_combo.addItem("")
        self.hint_fbi_combo.addItem("")
        self.hint_fbi_combo.addItem("")
        self.hint_fbi_combo.setObjectName(u"hint_fbi_combo")

        self.verticalLayout.addWidget(self.hint_fbi_combo)


        self.scroll_area_layout.addWidget(self.hint_fbi_group)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.scroll_area_layout.addItem(self.verticalSpacer)

        self.scroll_area.setWidget(self.scroll_area_contents)

        self.hint_layout.addWidget(self.scroll_area)

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

        self.hint_fbi_group.setTitle(QCoreApplication.translate("PresetMSRHints", u"Final Boss Item", None))
        self.hint_fbi_label.setText(QCoreApplication.translate("PresetMSRHints", u"<html><head/><body><p>After collecting all Metroid DNA, a message appears that says that the final boss can be fought and where to find them. Most of the final bosses require some item to either access or beat them, so an additional hint is provided that says where to find the item. This controls how precise that hint will be.</p><ul style=\"margin-top: 0px; margin-bottom: 0px; margin-left: 0px; margin-right: 0px; -qt-list-indent: 1;\"><li style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Proteus Ridley needs the Baby Metroid</li></ul><ul style=\"margin-top: 0px; margin-bottom: 0px; margin-left: 0px; margin-right: 0px; -qt-list-indent: 1;\"><li style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Diggernaut needs Bomb</li><li style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Metroid Queen needs Ice Beam</li"
                        "></ul><p><span style=\" font-weight:600;\">No hint</span>: No useful information is provided.</p><p><span style=\" font-weight:600;\">Show only the area name</span>: The hint reveals the area in which the Final Boss Item is located (&quot;Area 2&quot;, &quot;Area 7&quot;, etc.)</p><p><span style=\" font-weight:600;\">Show area and room name</span>: Same as above, but shows the exact room name.</p></body></html>", None))
        self.hint_fbi_combo.setItemText(0, QCoreApplication.translate("PresetMSRHints", u"No hints", None))
        self.hint_fbi_combo.setItemText(1, QCoreApplication.translate("PresetMSRHints", u"Show only the area name", None))
        self.hint_fbi_combo.setItemText(2, QCoreApplication.translate("PresetMSRHints", u"Show area and room name", None))

    # retranslateUi

