# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_prime_hunters_goal.ui'
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
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QMainWindow,
    QSizePolicy, QSlider, QVBoxLayout, QWidget)

from randovania.gui.lib.scroll_protected import ScrollProtectedSlider

class Ui_PresetHuntersGoal(object):
    def setupUi(self, PresetHuntersGoal):
        if not PresetHuntersGoal.objectName():
            PresetHuntersGoal.setObjectName(u"PresetHuntersGoal")
        PresetHuntersGoal.resize(383, 329)
        self.centralWidget = QWidget(PresetHuntersGoal)
        self.centralWidget.setObjectName(u"centralWidget")
        self.centralWidget.setMaximumSize(QSize(16777215, 16777215))
        self.goal_layout = QVBoxLayout(self.centralWidget)
        self.goal_layout.setSpacing(6)
        self.goal_layout.setContentsMargins(11, 11, 11, 11)
        self.goal_layout.setObjectName(u"goal_layout")
        self.goal_layout.setContentsMargins(4, 8, 4, 0)
        self.placed_description = QLabel(self.centralWidget)
        self.placed_description.setObjectName(u"placed_description")
        self.placed_description.setWordWrap(True)

        self.goal_layout.addWidget(self.placed_description)

        self.slider_layout = QHBoxLayout()
        self.slider_layout.setSpacing(6)
        self.slider_layout.setObjectName(u"slider_layout")
        self.placed_slider = ScrollProtectedSlider(self.centralWidget)
        self.placed_slider.setObjectName(u"placed_slider")
        self.placed_slider.setMaximum(8)
        self.placed_slider.setPageStep(2)
        self.placed_slider.setOrientation(Qt.Horizontal)
        self.placed_slider.setTickPosition(QSlider.TicksBelow)

        self.slider_layout.addWidget(self.placed_slider)

        self.placed_slider_label = QLabel(self.centralWidget)
        self.placed_slider_label.setObjectName(u"placed_slider_label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.placed_slider_label.sizePolicy().hasHeightForWidth())
        self.placed_slider_label.setSizePolicy(sizePolicy)
        self.placed_slider_label.setMinimumSize(QSize(20, 0))
        self.placed_slider_label.setAlignment(Qt.AlignCenter)

        self.slider_layout.addWidget(self.placed_slider_label)


        self.goal_layout.addLayout(self.slider_layout)

        PresetHuntersGoal.setCentralWidget(self.centralWidget)

        self.retranslateUi(PresetHuntersGoal)

        QMetaObject.connectSlotsByName(PresetHuntersGoal)
    # setupUi

    def retranslateUi(self, PresetHuntersGoal):
        PresetHuntersGoal.setWindowTitle(QCoreApplication.translate("PresetHuntersGoal", u"Goal", None))
        self.placed_description.setText(QCoreApplication.translate("PresetHuntersGoal", u"<html><head/><body><p>Controls how many Octoliths are needed in order to unlock Oubliette.</p></body></html>", None))
        self.placed_slider_label.setText(QCoreApplication.translate("PresetHuntersGoal", u"0", None))
    # retranslateUi

