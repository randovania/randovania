# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_fusion_goal.ui'
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
    QScrollArea, QSizePolicy, QSlider, QSpacerItem,
    QVBoxLayout, QWidget)

from randovania.gui.lib.scroll_protected import ScrollProtectedSlider

class Ui_PresetFusionGoal(object):
    def setupUi(self, PresetFusionGoal):
        if not PresetFusionGoal.objectName():
            PresetFusionGoal.setObjectName(u"PresetFusionGoal")
        PresetFusionGoal.resize(770, 472)
        self.centralWidget = QWidget(PresetFusionGoal)
        self.centralWidget.setObjectName(u"centralWidget")
        self.centralWidget.setMaximumSize(QSize(16777215, 16777215))
        self.goal_layout = QVBoxLayout(self.centralWidget)
        self.goal_layout.setSpacing(6)
        self.goal_layout.setContentsMargins(11, 11, 11, 11)
        self.goal_layout.setObjectName(u"goal_layout")
        self.goal_layout.setContentsMargins(4, 8, 4, 8)
        self.scrollArea = QScrollArea(self.centralWidget)
        self.scrollArea.setObjectName(u"scrollArea")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scrollArea.sizePolicy().hasHeightForWidth())
        self.scrollArea.setSizePolicy(sizePolicy)
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 760, 454))
        self.verticalLayout = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.description_label = QLabel(self.scrollAreaWidgetContents)
        self.description_label.setObjectName(u"description_label")
        self.description_label.setWordWrap(True)

        self.verticalLayout.addWidget(self.description_label)

        self.placed_label = QLabel(self.scrollAreaWidgetContents)
        self.placed_label.setObjectName(u"placed_label")
        self.placed_label.setWordWrap(True)

        self.verticalLayout.addWidget(self.placed_label)

        self.placed_slider_layout = QHBoxLayout()
        self.placed_slider_layout.setSpacing(6)
        self.placed_slider_layout.setObjectName(u"placed_slider_layout")
        self.placed_slider = ScrollProtectedSlider(self.scrollAreaWidgetContents)
        self.placed_slider.setObjectName(u"placed_slider")
        self.placed_slider.setMaximum(20)
        self.placed_slider.setPageStep(2)
        self.placed_slider.setOrientation(Qt.Horizontal)
        self.placed_slider.setTickPosition(QSlider.TicksBelow)

        self.placed_slider_layout.addWidget(self.placed_slider)

        self.placed_slider_label = QLabel(self.scrollAreaWidgetContents)
        self.placed_slider_label.setObjectName(u"placed_slider_label")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.placed_slider_label.sizePolicy().hasHeightForWidth())
        self.placed_slider_label.setSizePolicy(sizePolicy1)
        self.placed_slider_label.setMinimumSize(QSize(150, 0))
        self.placed_slider_label.setAlignment(Qt.AlignCenter)

        self.placed_slider_layout.addWidget(self.placed_slider_label)


        self.verticalLayout.addLayout(self.placed_slider_layout)

        self.required_label = QLabel(self.scrollAreaWidgetContents)
        self.required_label.setObjectName(u"required_label")
        self.required_label.setWordWrap(True)

        self.verticalLayout.addWidget(self.required_label)

        self.required_slider_layout = QHBoxLayout()
        self.required_slider_layout.setSpacing(6)
        self.required_slider_layout.setObjectName(u"required_slider_layout")
        self.required_slider = ScrollProtectedSlider(self.scrollAreaWidgetContents)
        self.required_slider.setObjectName(u"required_slider")
        self.required_slider.setMaximum(20)
        self.required_slider.setPageStep(2)
        self.required_slider.setOrientation(Qt.Horizontal)
        self.required_slider.setTickPosition(QSlider.TicksBelow)

        self.required_slider_layout.addWidget(self.required_slider)

        self.required_slider_label = QLabel(self.scrollAreaWidgetContents)
        self.required_slider_label.setObjectName(u"required_slider_label")
        sizePolicy1.setHeightForWidth(self.required_slider_label.sizePolicy().hasHeightForWidth())
        self.required_slider_label.setSizePolicy(sizePolicy1)
        self.required_slider_label.setMinimumSize(QSize(150, 0))
        self.required_slider_label.setAlignment(Qt.AlignCenter)

        self.required_slider_layout.addWidget(self.required_slider_label)


        self.verticalLayout.addLayout(self.required_slider_layout)

        self.spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.spacer)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.goal_layout.addWidget(self.scrollArea)

        PresetFusionGoal.setCentralWidget(self.centralWidget)

        self.retranslateUi(PresetFusionGoal)

        QMetaObject.connectSlotsByName(PresetFusionGoal)
    # setupUi

    def retranslateUi(self, PresetFusionGoal):
        PresetFusionGoal.setWindowTitle(QCoreApplication.translate("PresetFusionGoal", u"Goal", None))
        self.description_label.setText(QCoreApplication.translate("PresetFusionGoal", u"<html><head/><body><p>In addition to preparing for battle with the SA-X, it is now necessary to collect the escaped Infant Metroids in order to reach the Operations Room. Metroids can be found throughout the B.S.L, but they tend to be attracted to bosses for their energy.</p><p>The minimum and maximum are limited to 0 and 20 Infant Metroids. You can choose to place more Metroids than required.</p></body></html>", None))
        self.placed_label.setText(QCoreApplication.translate("PresetFusionGoal", u"<html><head/><body><p>Controls how many Infant Metroids will be placed in the game.</p></body></html>", None))
        self.placed_slider_label.setText(QCoreApplication.translate("PresetFusionGoal", u"0", None))
        self.required_label.setText(QCoreApplication.translate("PresetFusionGoal", u"<html><head/><body><p>Controls how many Infant Metroids are required to beat the game.</p></body></html>", None))
        self.required_slider_label.setText(QCoreApplication.translate("PresetFusionGoal", u"0", None))
    # retranslateUi

