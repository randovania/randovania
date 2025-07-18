# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_planets_zebeth_goal.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QGroupBox, QHBoxLayout,
    QLabel, QMainWindow, QSizePolicy, QSlider,
    QSpacerItem, QVBoxLayout, QWidget)

from randovania.gui.lib.scroll_protected import ScrollProtectedSlider

class Ui_PresetPlanetsZebethGoal(object):
    def setupUi(self, PresetPlanetsZebethGoal):
        if not PresetPlanetsZebethGoal.objectName():
            PresetPlanetsZebethGoal.setObjectName(u"PresetPlanetsZebethGoal")
        PresetPlanetsZebethGoal.resize(1196, 274)
        self.centralWidget = QWidget(PresetPlanetsZebethGoal)
        self.centralWidget.setObjectName(u"centralWidget")
        self.centralWidget.setMaximumSize(QSize(16777215, 16777215))
        self.goal_layout = QVBoxLayout(self.centralWidget)
        self.goal_layout.setSpacing(6)
        self.goal_layout.setContentsMargins(11, 11, 11, 11)
        self.goal_layout.setObjectName(u"goal_layout")
        self.goal_layout.setContentsMargins(4, 8, 4, 8)
        self.description_label = QLabel(self.centralWidget)
        self.description_label.setObjectName(u"description_label")
        self.description_label.setWordWrap(True)

        self.goal_layout.addWidget(self.description_label)

        self.keys_slider_layout = QHBoxLayout()
        self.keys_slider_layout.setSpacing(6)
        self.keys_slider_layout.setObjectName(u"keys_slider_layout")
        self.keys_slider = ScrollProtectedSlider(self.centralWidget)
        self.keys_slider.setObjectName(u"keys_slider")
        self.keys_slider.setMaximum(9)
        self.keys_slider.setPageStep(2)
        self.keys_slider.setOrientation(Qt.Horizontal)
        self.keys_slider.setTickPosition(QSlider.TicksBelow)

        self.keys_slider_layout.addWidget(self.keys_slider)

        self.keys_slider_label = QLabel(self.centralWidget)
        self.keys_slider_label.setObjectName(u"keys_slider_label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.keys_slider_label.sizePolicy().hasHeightForWidth())
        self.keys_slider_label.setSizePolicy(sizePolicy)
        self.keys_slider_label.setMinimumSize(QSize(20, 0))
        self.keys_slider_label.setAlignment(Qt.AlignCenter)

        self.keys_slider_layout.addWidget(self.keys_slider_label)


        self.goal_layout.addLayout(self.keys_slider_layout)

        self.placement_group = QGroupBox(self.centralWidget)
        self.placement_group.setObjectName(u"placement_group")
        self.placement_layout = QVBoxLayout(self.placement_group)
        self.placement_layout.setSpacing(6)
        self.placement_layout.setContentsMargins(11, 11, 11, 11)
        self.placement_layout.setObjectName(u"placement_layout")
        self.placement_label = QLabel(self.placement_group)
        self.placement_label.setObjectName(u"placement_label")
        self.placement_label.setWordWrap(True)

        self.placement_layout.addWidget(self.placement_label)

        self.vanilla_tourian_keys_check = QCheckBox(self.placement_group)
        self.vanilla_tourian_keys_check.setObjectName(u"vanilla_tourian_keys_check")
        self.vanilla_tourian_keys_check.setChecked(True)

        self.placement_layout.addWidget(self.vanilla_tourian_keys_check)


        self.goal_layout.addWidget(self.placement_group)

        self.spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.goal_layout.addItem(self.spacer)

        PresetPlanetsZebethGoal.setCentralWidget(self.centralWidget)

        self.retranslateUi(PresetPlanetsZebethGoal)

        QMetaObject.connectSlotsByName(PresetPlanetsZebethGoal)
    # setupUi

    def retranslateUi(self, PresetPlanetsZebethGoal):
        PresetPlanetsZebethGoal.setWindowTitle(QCoreApplication.translate("PresetPlanetsZebethGoal", u"Goal", None))
        self.description_label.setText(QCoreApplication.translate("PresetPlanetsZebethGoal", u"<html><head/><body><p>In order to reach Mother Brain it's now necessary to have keys.</p></body></html>", None))
        self.keys_slider_label.setText(QCoreApplication.translate("PresetPlanetsZebethGoal", u"0", None))
        self.placement_group.setTitle(QCoreApplication.translate("PresetPlanetsZebethGoal", u"Placement", None))
        self.placement_label.setText(QCoreApplication.translate("PresetPlanetsZebethGoal", u"<html><head/><body><p>The following options limit where Keys will be placed. There can only be 9 Keys in total due to limited space in Brinstar - Entrance to Tourian.</p></body></html>", None))
#if QT_CONFIG(tooltip)
        self.vanilla_tourian_keys_check.setToolTip(QCoreApplication.translate("PresetPlanetsZebethGoal", u"<html><head/><body><p>This will place only 2 keys and will force the keys on Kraid and Ridley</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.vanilla_tourian_keys_check.setText(QCoreApplication.translate("PresetPlanetsZebethGoal", u"Vanilla Tourian Keys", None))
    # retranslateUi

