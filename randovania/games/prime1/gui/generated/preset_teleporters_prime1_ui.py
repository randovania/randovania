# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_teleporters_prime1.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QFrame, QGridLayout,
    QGroupBox, QLabel, QMainWindow, QScrollArea,
    QSizePolicy, QVBoxLayout, QWidget)

from randovania.gui.lib.scroll_protected import ScrollProtectedComboBox

class Ui_PresetTeleportersPrime1(object):
    def setupUi(self, PresetTeleportersPrime1):
        if not PresetTeleportersPrime1.objectName():
            PresetTeleportersPrime1.setObjectName(u"PresetTeleportersPrime1")
        PresetTeleportersPrime1.resize(505, 463)
        self.centralWidget = QWidget(PresetTeleportersPrime1)
        self.centralWidget.setObjectName(u"centralWidget")
        self.centralWidget.setMaximumSize(QSize(16777215, 16777215))
        self.teleporter_parent_layout = QVBoxLayout(self.centralWidget)
        self.teleporter_parent_layout.setSpacing(6)
        self.teleporter_parent_layout.setContentsMargins(11, 11, 11, 11)
        self.teleporter_parent_layout.setObjectName(u"teleporter_parent_layout")
        self.teleporter_parent_layout.setContentsMargins(0, 0, 0, 0)
        self.teleporter_scroll_area = QScrollArea(self.centralWidget)
        self.teleporter_scroll_area.setObjectName(u"teleporter_scroll_area")
        self.teleporter_scroll_area.setWidgetResizable(True)
        self.teleporter_scroll_area_contents = QWidget()
        self.teleporter_scroll_area_contents.setObjectName(u"teleporter_scroll_area_contents")
        self.teleporter_scroll_area_contents.setGeometry(QRect(0, 0, 503, 461))
        self.teleporters_layout = QVBoxLayout(self.teleporter_scroll_area_contents)
        self.teleporters_layout.setSpacing(6)
        self.teleporters_layout.setContentsMargins(11, 11, 11, 11)
        self.teleporters_layout.setObjectName(u"teleporters_layout")
        self.teleporters_layout.setContentsMargins(4, 6, 4, 0)
        self.teleporters_combo = ScrollProtectedComboBox(self.teleporter_scroll_area_contents)
        self.teleporters_combo.setObjectName(u"teleporters_combo")

        self.teleporters_layout.addWidget(self.teleporters_combo)

        self.teleporters_description_label = QLabel(self.teleporter_scroll_area_contents)
        self.teleporters_description_label.setObjectName(u"teleporters_description_label")
        self.teleporters_description_label.setScaledContents(True)
        self.teleporters_description_label.setWordWrap(True)

        self.teleporters_layout.addWidget(self.teleporters_description_label)

        self.teleporters_line_2 = QFrame(self.teleporter_scroll_area_contents)
        self.teleporters_line_2.setObjectName(u"teleporters_line_2")
        self.teleporters_line_2.setFrameShape(QFrame.Shape.HLine)
        self.teleporters_line_2.setFrameShadow(QFrame.Shadow.Sunken)

        self.teleporters_layout.addWidget(self.teleporters_line_2)

        self.skip_final_bosses_check = QCheckBox(self.teleporter_scroll_area_contents)
        self.skip_final_bosses_check.setObjectName(u"skip_final_bosses_check")

        self.teleporters_layout.addWidget(self.skip_final_bosses_check)

        self.skip_final_bosses_label = QLabel(self.teleporter_scroll_area_contents)
        self.skip_final_bosses_label.setObjectName(u"skip_final_bosses_label")
        self.skip_final_bosses_label.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.skip_final_bosses_label.setWordWrap(True)

        self.teleporters_layout.addWidget(self.skip_final_bosses_label)

        self.teleporters_line_3 = QFrame(self.teleporter_scroll_area_contents)
        self.teleporters_line_3.setObjectName(u"teleporters_line_3")
        self.teleporters_line_3.setFrameShape(QFrame.Shape.HLine)
        self.teleporters_line_3.setFrameShadow(QFrame.Shadow.Sunken)

        self.teleporters_layout.addWidget(self.teleporters_line_3)

        self.teleporters_source_group = QGroupBox(self.teleporter_scroll_area_contents)
        self.teleporters_source_group.setObjectName(u"teleporters_source_group")
        self.teleporters_source_layout = QGridLayout(self.teleporters_source_group)
        self.teleporters_source_layout.setSpacing(3)
        self.teleporters_source_layout.setContentsMargins(11, 11, 11, 11)
        self.teleporters_source_layout.setObjectName(u"teleporters_source_layout")
        self.teleporters_source_layout.setContentsMargins(1, 1, 1, 1)

        self.teleporters_layout.addWidget(self.teleporters_source_group)

        self.teleporters_target_group = QGroupBox(self.teleporter_scroll_area_contents)
        self.teleporters_target_group.setObjectName(u"teleporters_target_group")
        self.teleporters_target_layout = QGridLayout(self.teleporters_target_group)
        self.teleporters_target_layout.setSpacing(3)
        self.teleporters_target_layout.setContentsMargins(11, 11, 11, 11)
        self.teleporters_target_layout.setObjectName(u"teleporters_target_layout")
        self.teleporters_target_layout.setContentsMargins(1, 1, 1, 1)

        self.teleporters_layout.addWidget(self.teleporters_target_group)

        self.teleporter_scroll_area.setWidget(self.teleporter_scroll_area_contents)

        self.teleporter_parent_layout.addWidget(self.teleporter_scroll_area)

        PresetTeleportersPrime1.setCentralWidget(self.centralWidget)

        self.retranslateUi(PresetTeleportersPrime1)

        QMetaObject.connectSlotsByName(PresetTeleportersPrime1)
    # setupUi

    def retranslateUi(self, PresetTeleportersPrime1):
        PresetTeleportersPrime1.setWindowTitle(QCoreApplication.translate("PresetTeleportersPrime1", u"Elevators", None))
        self.teleporters_description_label.setText(QCoreApplication.translate("PresetTeleportersPrime1", u"<html><head/><body><p>&lt;description generated dynamically&gt;</p></body></html>", None))
        self.skip_final_bosses_check.setText(QCoreApplication.translate("PresetTeleportersPrime1", u"Go directly to credits from Artifact Temple", None))
        self.skip_final_bosses_label.setText(QCoreApplication.translate("PresetTeleportersPrime1", u"<html><head/><body>\n"
"        <p>Change the teleport in Artifact Temple to go directly to the credits, skipping the final bosses.</p>\n"
"        <p>This changes the requirements to <span style=\" font-weight:600;\">not need the final bosses</span>,\n"
"        turning certain items optional such as Plasma Beam.</p></body></html>", None))
        self.teleporters_source_group.setTitle(QCoreApplication.translate("PresetTeleportersPrime1", u"Elevators to randomize", None))
        self.teleporters_target_group.setTitle(QCoreApplication.translate("PresetTeleportersPrime1", u"Valid teleporter targets", None))
    # retranslateUi

