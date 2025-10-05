# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_teleporters_dread.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QGridLayout, QGroupBox,
    QLabel, QMainWindow, QScrollArea, QSizePolicy,
    QVBoxLayout, QWidget)

from randovania.gui.lib.scroll_protected import ScrollProtectedComboBox

class Ui_PresetTeleportersDread(object):
    def setupUi(self, PresetTeleportersDread):
        if not PresetTeleportersDread.objectName():
            PresetTeleportersDread.setObjectName(u"PresetTeleportersDread")
        PresetTeleportersDread.resize(505, 463)
        self.centralWidget = QWidget(PresetTeleportersDread)
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

        self.teleporters_line = QFrame(self.teleporter_scroll_area_contents)
        self.teleporters_line.setObjectName(u"teleporters_line")
        self.teleporters_line.setFrameShape(QFrame.Shape.HLine)
        self.teleporters_line.setFrameShadow(QFrame.Shadow.Sunken)

        self.teleporters_layout.addWidget(self.teleporters_line)

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

        PresetTeleportersDread.setCentralWidget(self.centralWidget)

        self.retranslateUi(PresetTeleportersDread)

        QMetaObject.connectSlotsByName(PresetTeleportersDread)
    # setupUi

    def retranslateUi(self, PresetTeleportersDread):
        PresetTeleportersDread.setWindowTitle(QCoreApplication.translate("PresetTeleportersDread", u"Transporters", None))
        self.teleporters_description_label.setText(QCoreApplication.translate("PresetTeleportersDread", u"<html><head/><body><p>&lt;description generated dynamically&gt;</p></body></html>", None))
        self.teleporters_source_group.setTitle(QCoreApplication.translate("PresetTeleportersDread", u"Transporters to randomize", None))
        self.teleporters_target_group.setTitle(QCoreApplication.translate("PresetTeleportersDread", u"Valid teleporter targets", None))
    # retranslateUi

