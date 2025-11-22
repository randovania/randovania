# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_planets_zebeth_patches.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QFrame, QLabel,
    QMainWindow, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

class Ui_PresetPlanetsZebethPatches(object):
    def setupUi(self, PresetPlanetsZebethPatches):
        if not PresetPlanetsZebethPatches.objectName():
            PresetPlanetsZebethPatches.setObjectName(u"PresetPlanetsZebethPatches")
        PresetPlanetsZebethPatches.resize(466, 599)
        self.centralWidget = QWidget(PresetPlanetsZebethPatches)
        self.centralWidget.setObjectName(u"centralWidget")
        self.centralWidget.setMaximumSize(QSize(16777215, 16777215))
        self.verticalLayout = QVBoxLayout(self.centralWidget)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(4, 4, 4, 4)
        self.warp_to_start_check = QCheckBox(self.centralWidget)
        self.warp_to_start_check.setObjectName(u"warp_to_start_check")

        self.verticalLayout.addWidget(self.warp_to_start_check)

        self.warp_to_start_label = QLabel(self.centralWidget)
        self.warp_to_start_label.setObjectName(u"warp_to_start_label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.warp_to_start_label.sizePolicy().hasHeightForWidth())
        self.warp_to_start_label.setSizePolicy(sizePolicy)
        self.warp_to_start_label.setMaximumSize(QSize(16777215, 70))
        self.warp_to_start_label.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        self.warp_to_start_label.setWordWrap(True)

        self.verticalLayout.addWidget(self.warp_to_start_label)

        self.open_missile_doors_with_one_missile_line = QFrame(self.centralWidget)
        self.open_missile_doors_with_one_missile_line.setObjectName(u"open_missile_doors_with_one_missile_line")
        self.open_missile_doors_with_one_missile_line.setFrameShape(QFrame.Shape.HLine)
        self.open_missile_doors_with_one_missile_line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.open_missile_doors_with_one_missile_line)

        self.open_missile_doors_with_one_missile_check = QCheckBox(self.centralWidget)
        self.open_missile_doors_with_one_missile_check.setObjectName(u"open_missile_doors_with_one_missile_check")

        self.verticalLayout.addWidget(self.open_missile_doors_with_one_missile_check)

        self.open_missile_doors_with_one_missile_label = QLabel(self.centralWidget)
        self.open_missile_doors_with_one_missile_label.setObjectName(u"open_missile_doors_with_one_missile_label")
        self.open_missile_doors_with_one_missile_label.setWordWrap(True)

        self.verticalLayout.addWidget(self.open_missile_doors_with_one_missile_label)

        self.allow_downward_shots_line = QFrame(self.centralWidget)
        self.allow_downward_shots_line.setObjectName(u"allow_downward_shots_line")
        self.allow_downward_shots_line.setFrameShape(QFrame.Shape.HLine)
        self.allow_downward_shots_line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.allow_downward_shots_line)

        self.allow_downward_shots_check = QCheckBox(self.centralWidget)
        self.allow_downward_shots_check.setObjectName(u"allow_downward_shots_check")

        self.verticalLayout.addWidget(self.allow_downward_shots_check)

        self.allow_downward_shots_label = QLabel(self.centralWidget)
        self.allow_downward_shots_label.setObjectName(u"allow_downward_shots_label")

        self.verticalLayout.addWidget(self.allow_downward_shots_label)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        PresetPlanetsZebethPatches.setCentralWidget(self.centralWidget)

        self.retranslateUi(PresetPlanetsZebethPatches)

        QMetaObject.connectSlotsByName(PresetPlanetsZebethPatches)
    # setupUi

    def retranslateUi(self, PresetPlanetsZebethPatches):
        PresetPlanetsZebethPatches.setWindowTitle(QCoreApplication.translate("PresetPlanetsZebethPatches", u"Other", None))
        self.warp_to_start_check.setText(QCoreApplication.translate("PresetPlanetsZebethPatches", u"Warp to start", None))
        self.warp_to_start_label.setText(QCoreApplication.translate("PresetPlanetsZebethPatches", u"Allows you to warp to start from pause menu.", None))
        self.open_missile_doors_with_one_missile_check.setText(QCoreApplication.translate("PresetPlanetsZebethPatches", u"Open Missile doors with one Missile", None))
        self.open_missile_doors_with_one_missile_label.setText(QCoreApplication.translate("PresetPlanetsZebethPatches", u"With this option enabled, only one missile is required to open red doors instead of 5.", None))
        self.allow_downward_shots_check.setText(QCoreApplication.translate("PresetPlanetsZebethPatches", u"Allow downward shots", None))
        self.allow_downward_shots_label.setText(QCoreApplication.translate("PresetPlanetsZebethPatches", u"Allows the player to shoot below.", None))
    # retranslateUi

