# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_dread_goal.ui'
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

class Ui_PresetDreadGoal(object):
    def setupUi(self, PresetDreadGoal):
        if not PresetDreadGoal.objectName():
            PresetDreadGoal.setObjectName(u"PresetDreadGoal")
        PresetDreadGoal.resize(768, 274)
        self.centralWidget = QWidget(PresetDreadGoal)
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

        self.dna_slider_layout = QHBoxLayout()
        self.dna_slider_layout.setSpacing(6)
        self.dna_slider_layout.setObjectName(u"dna_slider_layout")
        self.dna_slider = ScrollProtectedSlider(self.centralWidget)
        self.dna_slider.setObjectName(u"dna_slider")
        self.dna_slider.setMaximum(12)
        self.dna_slider.setPageStep(2)
        self.dna_slider.setOrientation(Qt.Horizontal)
        self.dna_slider.setTickPosition(QSlider.TicksBelow)

        self.dna_slider_layout.addWidget(self.dna_slider)

        self.dna_slider_label = QLabel(self.centralWidget)
        self.dna_slider_label.setObjectName(u"dna_slider_label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.dna_slider_label.sizePolicy().hasHeightForWidth())
        self.dna_slider_label.setSizePolicy(sizePolicy)
        self.dna_slider_label.setMinimumSize(QSize(20, 0))
        self.dna_slider_label.setAlignment(Qt.AlignCenter)

        self.dna_slider_layout.addWidget(self.dna_slider_label)


        self.goal_layout.addLayout(self.dna_slider_layout)

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

        self.prefer_emmi_check = QCheckBox(self.placement_group)
        self.prefer_emmi_check.setObjectName(u"prefer_emmi_check")

        self.placement_layout.addWidget(self.prefer_emmi_check)

        self.prefer_major_bosses_check = QCheckBox(self.placement_group)
        self.prefer_major_bosses_check.setObjectName(u"prefer_major_bosses_check")

        self.placement_layout.addWidget(self.prefer_major_bosses_check)


        self.goal_layout.addWidget(self.placement_group)

        self.spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.goal_layout.addItem(self.spacer)

        PresetDreadGoal.setCentralWidget(self.centralWidget)

        self.retranslateUi(PresetDreadGoal)

        QMetaObject.connectSlotsByName(PresetDreadGoal)
    # setupUi

    def retranslateUi(self, PresetDreadGoal):
        PresetDreadGoal.setWindowTitle(QCoreApplication.translate("PresetDreadGoal", u"Goal", None))
        self.description_label.setText(QCoreApplication.translate("PresetDreadGoal", u"<html><head/><body><p>In addition to just reaching Itorash, it's now necessary to collect Metroid DNA in order to reach Raven Beak.</p><p>A Navigation Station has been added to Itorash entrance that tells you where the DNA can be found.</p></body></html>", None))
        self.dna_slider_label.setText(QCoreApplication.translate("PresetDreadGoal", u"0", None))
        self.placement_group.setTitle(QCoreApplication.translate("PresetDreadGoal", u"Placement", None))
        self.placement_label.setText(QCoreApplication.translate("PresetDreadGoal", u"<html><head/><body><p>The following options limit where Metroid DNA will be placed. There can only be as many DNA shuffled as there are preferred locations enabled. Each option adds 6 locations, up to a total of 12.</p></body></html>", None))
        self.prefer_emmi_check.setText(QCoreApplication.translate("PresetDreadGoal", u"Prefer E.M.M.I.", None))
        self.prefer_major_bosses_check.setText(QCoreApplication.translate("PresetDreadGoal", u"Prefer major bosses (Corpius, Drogyga, Escue, Experiment Z-57, Golzuna and Kraid)", None))
    # retranslateUi

