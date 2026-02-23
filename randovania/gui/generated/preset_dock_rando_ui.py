# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_dock_rando.ui'
##
## Created by: Qt User Interface Compiler version 6.10.0
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
from PySide6.QtWidgets import (QApplication, QComboBox, QFrame, QGroupBox,
    QHBoxLayout, QLabel, QMainWindow, QScrollArea,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

class Ui_PresetDockRando(object):
    def setupUi(self, PresetDockRando):
        if not PresetDockRando.objectName():
            PresetDockRando.setObjectName(u"PresetDockRando")
        PresetDockRando.resize(476, 628)
        self.centralWidget = QWidget(PresetDockRando)
        self.centralWidget.setObjectName(u"centralWidget")
        self.centralWidget.setMaximumSize(QSize(16777215, 16777215))
        self.main_layout = QVBoxLayout(self.centralWidget)
        self.main_layout.setSpacing(6)
        self.main_layout.setContentsMargins(11, 11, 11, 11)
        self.main_layout.setObjectName(u"main_layout")
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_area = QScrollArea(self.centralWidget)
        self.scroll_area.setObjectName(u"scroll_area")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area_contents = QWidget()
        self.scroll_area_contents.setObjectName(u"scroll_area_contents")
        self.scroll_area_contents.setGeometry(QRect(0, 0, 474, 626))
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scroll_area_contents.sizePolicy().hasHeightForWidth())
        self.scroll_area_contents.setSizePolicy(sizePolicy)
        self.scroll_area_layout = QVBoxLayout(self.scroll_area_contents)
        self.scroll_area_layout.setSpacing(6)
        self.scroll_area_layout.setContentsMargins(11, 11, 11, 11)
        self.scroll_area_layout.setObjectName(u"scroll_area_layout")
        self.scroll_area_layout.setContentsMargins(1, 1, 1, 0)
        self.settings_group = QGroupBox(self.scroll_area_contents)
        self.settings_group.setObjectName(u"settings_group")
        self.settings_layout = QVBoxLayout(self.settings_group)
        self.settings_layout.setSpacing(6)
        self.settings_layout.setContentsMargins(11, 11, 11, 11)
        self.settings_layout.setObjectName(u"settings_layout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.mode_label = QLabel(self.settings_group)
        self.mode_label.setObjectName(u"mode_label")

        self.horizontalLayout.addWidget(self.mode_label)

        self.mode_combo = QComboBox(self.settings_group)
        self.mode_combo.setObjectName(u"mode_combo")
        self.mode_combo.setInsertPolicy(QComboBox.InsertPolicy.InsertAtCurrent)

        self.horizontalLayout.addWidget(self.mode_combo)


        self.settings_layout.addLayout(self.horizontalLayout)

        self.mode_description = QLabel(self.settings_group)
        self.mode_description.setObjectName(u"mode_description")

        self.settings_layout.addWidget(self.mode_description)

        self.line = QFrame(self.settings_group)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.settings_layout.addWidget(self.line)

        self.multiworld_label = QLabel(self.settings_group)
        self.multiworld_label.setObjectName(u"multiworld_label")

        self.settings_layout.addWidget(self.multiworld_label)


        self.scroll_area_layout.addWidget(self.settings_group)

        self.dock_types_group = QGroupBox(self.scroll_area_contents)
        self.dock_types_group.setObjectName(u"dock_types_group")
        self.verticalLayout = QVBoxLayout(self.dock_types_group)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.desc_layouts = QHBoxLayout()
        self.desc_layouts.setSpacing(6)
        self.desc_layouts.setObjectName(u"desc_layouts")
        self.change_from_desc = QLabel(self.dock_types_group)
        self.change_from_desc.setObjectName(u"change_from_desc")
        self.change_from_desc.setTextFormat(Qt.TextFormat.MarkdownText)
        self.change_from_desc.setWordWrap(True)

        self.desc_layouts.addWidget(self.change_from_desc)

        self.change_to_desc = QLabel(self.dock_types_group)
        self.change_to_desc.setObjectName(u"change_to_desc")
        self.change_to_desc.setTextFormat(Qt.TextFormat.MarkdownText)
        self.change_to_desc.setWordWrap(True)

        self.desc_layouts.addWidget(self.change_to_desc)


        self.verticalLayout.addLayout(self.desc_layouts)


        self.scroll_area_layout.addWidget(self.dock_types_group)

        self.spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.scroll_area_layout.addItem(self.spacer)

        self.scroll_area.setWidget(self.scroll_area_contents)

        self.main_layout.addWidget(self.scroll_area)

        PresetDockRando.setCentralWidget(self.centralWidget)

        self.retranslateUi(PresetDockRando)

        QMetaObject.connectSlotsByName(PresetDockRando)
    # setupUi

    def retranslateUi(self, PresetDockRando):
        PresetDockRando.setWindowTitle(QCoreApplication.translate("PresetDockRando", u"Door Locks", None))
        self.settings_group.setTitle(QCoreApplication.translate("PresetDockRando", u"Settings", None))
        self.mode_label.setText(QCoreApplication.translate("PresetDockRando", u"Randomization Mode", None))
        self.mode_description.setText(QCoreApplication.translate("PresetDockRando", u"Original door locks.", None))
        self.multiworld_label.setText(QCoreApplication.translate("PresetDockRando", u"<html><head/><body><p>The selected mode is <span style=\" font-weight:700;\">not</span> compatible with multiworld sessions.</p></body></html>", None))
        self.dock_types_group.setTitle(QCoreApplication.translate("PresetDockRando", u"Door Types", None))
        self.change_from_desc.setText(QCoreApplication.translate("PresetDockRando", u"**Doors to Change**\n"
"\n"
"Which door locks can be changed.", None))
        self.change_to_desc.setText(QCoreApplication.translate("PresetDockRando", u"**Change Doors To**\n"
"\n"
"Which locks a door can be changed to.", None))
    # retranslateUi

