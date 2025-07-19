# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_echoes_goal.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QHBoxLayout, QLabel,
    QMainWindow, QSizePolicy, QSlider, QSpacerItem,
    QVBoxLayout, QWidget)

from randovania.gui.lib.scroll_protected import ScrollProtectedSlider

class Ui_PresetEchoesGoal(object):
    def setupUi(self, PresetEchoesGoal):
        if not PresetEchoesGoal.objectName():
            PresetEchoesGoal.setObjectName(u"PresetEchoesGoal")
        PresetEchoesGoal.resize(562, 459)
        self.centralWidget = QWidget(PresetEchoesGoal)
        self.centralWidget.setObjectName(u"centralWidget")
        self.centralWidget.setMaximumSize(QSize(16777215, 16777215))
        self.goal_layout = QVBoxLayout(self.centralWidget)
        self.goal_layout.setSpacing(6)
        self.goal_layout.setContentsMargins(11, 11, 11, 11)
        self.goal_layout.setObjectName(u"goal_layout")
        self.goal_layout.setContentsMargins(4, 8, 4, 8)
        self.skytemple_description = QLabel(self.centralWidget)
        self.skytemple_description.setObjectName(u"skytemple_description")
        self.skytemple_description.setWordWrap(True)

        self.goal_layout.addWidget(self.skytemple_description)

        self.skytemple_combo = QComboBox(self.centralWidget)
        self.skytemple_combo.addItem("")
        self.skytemple_combo.addItem("")
        self.skytemple_combo.addItem("")
        self.skytemple_combo.setObjectName(u"skytemple_combo")

        self.goal_layout.addWidget(self.skytemple_combo)

        self.skytemple_slider_layout = QHBoxLayout()
        self.skytemple_slider_layout.setSpacing(6)
        self.skytemple_slider_layout.setObjectName(u"skytemple_slider_layout")
        self.skytemple_slider = ScrollProtectedSlider(self.centralWidget)
        self.skytemple_slider.setObjectName(u"skytemple_slider")
        self.skytemple_slider.setMaximum(9)
        self.skytemple_slider.setPageStep(2)
        self.skytemple_slider.setOrientation(Qt.Horizontal)
        self.skytemple_slider.setTickPosition(QSlider.TicksBelow)

        self.skytemple_slider_layout.addWidget(self.skytemple_slider)

        self.skytemple_slider_label = QLabel(self.centralWidget)
        self.skytemple_slider_label.setObjectName(u"skytemple_slider_label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.skytemple_slider_label.sizePolicy().hasHeightForWidth())
        self.skytemple_slider_label.setSizePolicy(sizePolicy)
        self.skytemple_slider_label.setMinimumSize(QSize(20, 0))
        self.skytemple_slider_label.setAlignment(Qt.AlignCenter)

        self.skytemple_slider_layout.addWidget(self.skytemple_slider_label)


        self.goal_layout.addLayout(self.skytemple_slider_layout)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.goal_layout.addItem(self.horizontalSpacer)

        PresetEchoesGoal.setCentralWidget(self.centralWidget)

        self.retranslateUi(PresetEchoesGoal)

        QMetaObject.connectSlotsByName(PresetEchoesGoal)
    # setupUi

    def retranslateUi(self, PresetEchoesGoal):
        PresetEchoesGoal.setWindowTitle(QCoreApplication.translate("PresetEchoesGoal", u"Goal", None))
        self.skytemple_description.setText(QCoreApplication.translate("PresetEchoesGoal", u"<html><head/><body><p>Controls where the Sky Temple Keys will be located.</p><p>All Guardians and Sub-Guardians: One key will be placed in each of the guardians and sub-guardians.<br/>Guardians: One key will be placed as the reward of each of the guardians.<br/>Collect Sky Temple Keys: A configurable quantity will be shuffled over the game world.</p><p>The Guardians are: Amorbis, Chykka and Quadraxis.<br/>The Sub-Guardians are: Bomb Guardian, Jump Guardian, Boost Guardian, Grapple Guardian, Spider Guardian and Power Bomb Guardian.</p><p>You can always check Sky Temple Gateway for hints where the keys were placed.</p></body></html>", None))
        self.skytemple_combo.setItemText(0, QCoreApplication.translate("PresetEchoesGoal", u"Guardians and Sub-Guardians", None))
        self.skytemple_combo.setItemText(1, QCoreApplication.translate("PresetEchoesGoal", u"Guardians", None))
        self.skytemple_combo.setItemText(2, QCoreApplication.translate("PresetEchoesGoal", u"Collect Sky Temple Keys", None))

        self.skytemple_slider_label.setText(QCoreApplication.translate("PresetEchoesGoal", u"0", None))
    # retranslateUi

