# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_fusion_goal.ui'
##
## Created by: Qt User Interface Compiler version 6.6.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import *  # type: ignore
from PySide6.QtGui import *  # type: ignore
from PySide6.QtWidgets import *  # type: ignore

class Ui_PresetFusionGoal(object):
    def setupUi(self, PresetFusionGoal):
        if not PresetFusionGoal.objectName():
            PresetFusionGoal.setObjectName(u"PresetFusionGoal")
        PresetFusionGoal.resize(1196, 344)
        self.centralWidget = QWidget(PresetFusionGoal)
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

        self.placed_label = QLabel(self.centralWidget)
        self.placed_label.setObjectName(u"placed_label")
        self.placed_label.setWordWrap(True)

        self.goal_layout.addWidget(self.placed_label)

        self.placed_slider_layout = QHBoxLayout()
        self.placed_slider_layout.setSpacing(6)
        self.placed_slider_layout.setObjectName(u"placed_slider_layout")
        self.placed_slider = QSlider(self.centralWidget)
        self.placed_slider.setObjectName(u"placed_slider")
        self.placed_slider.setMaximum(46)
        self.placed_slider.setPageStep(2)
        self.placed_slider.setOrientation(Qt.Horizontal)
        self.placed_slider.setTickPosition(QSlider.TicksBelow)

        self.placed_slider_layout.addWidget(self.placed_slider)

        self.placed_slider_label = QLabel(self.centralWidget)
        self.placed_slider_label.setObjectName(u"placed_slider_label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.placed_slider_label.sizePolicy().hasHeightForWidth())
        self.placed_slider_label.setSizePolicy(sizePolicy)
        self.placed_slider_label.setMinimumSize(QSize(150, 0))
        self.placed_slider_label.setAlignment(Qt.AlignCenter)

        self.placed_slider_layout.addWidget(self.placed_slider_label)


        self.goal_layout.addLayout(self.placed_slider_layout)

        self.required_label = QLabel(self.centralWidget)
        self.required_label.setObjectName(u"required_label")
        self.required_label.setWordWrap(True)

        self.goal_layout.addWidget(self.required_label)

        self.required_slider_layout = QHBoxLayout()
        self.required_slider_layout.setSpacing(6)
        self.required_slider_layout.setObjectName(u"required_slider_layout")
        self.required_slider = QSlider(self.centralWidget)
        self.required_slider.setObjectName(u"required_slider")
        self.required_slider.setMaximum(46)
        self.required_slider.setPageStep(2)
        self.required_slider.setOrientation(Qt.Horizontal)
        self.required_slider.setTickPosition(QSlider.TicksBelow)

        self.required_slider_layout.addWidget(self.required_slider)

        self.required_slider_label = QLabel(self.centralWidget)
        self.required_slider_label.setObjectName(u"required_slider_label")
        sizePolicy.setHeightForWidth(self.required_slider_label.sizePolicy().hasHeightForWidth())
        self.required_slider_label.setSizePolicy(sizePolicy)
        self.required_slider_label.setMinimumSize(QSize(150, 0))
        self.required_slider_label.setAlignment(Qt.AlignCenter)

        self.required_slider_layout.addWidget(self.required_slider_label)


        self.goal_layout.addLayout(self.required_slider_layout)

        self.placement_group = QGroupBox(self.centralWidget)
        self.placement_group.setObjectName(u"placement_group")
        self.placement_layout = QVBoxLayout(self.placement_group)
        self.placement_layout.setSpacing(6)
        self.placement_layout.setContentsMargins(11, 11, 11, 11)
        self.placement_layout.setObjectName(u"placement_layout")
        self.restrict_placement_radiobutton = QRadioButton(self.placement_group)
        self.restrict_placement_radiobutton.setObjectName(u"restrict_placement_radiobutton")

        self.placement_layout.addWidget(self.restrict_placement_radiobutton)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setSpacing(6)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(20, -1, -1, -1)
        self.restrict_placement_label = QLabel(self.placement_group)
        self.restrict_placement_label.setObjectName(u"restrict_placement_label")
        self.restrict_placement_label.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.restrict_placement_label)

        self.prefer_bosses_check = QCheckBox(self.placement_group)
        self.prefer_bosses_check.setObjectName(u"prefer_bosses_check")

        self.verticalLayout_2.addWidget(self.prefer_bosses_check)


        self.placement_layout.addLayout(self.verticalLayout_2)

        self.free_placement_radiobutton = QRadioButton(self.placement_group)
        self.free_placement_radiobutton.setObjectName(u"free_placement_radiobutton")

        self.placement_layout.addWidget(self.free_placement_radiobutton)

        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setSpacing(6)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(20, -1, -1, -1)
        self.free_placement_label = QLabel(self.placement_group)
        self.free_placement_label.setObjectName(u"free_placement_label")

        self.verticalLayout_3.addWidget(self.free_placement_label)


        self.placement_layout.addLayout(self.verticalLayout_3)


        self.goal_layout.addWidget(self.placement_group)

        self.spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.goal_layout.addItem(self.spacer)

        PresetFusionGoal.setCentralWidget(self.centralWidget)

        self.retranslateUi(PresetFusionGoal)

        QMetaObject.connectSlotsByName(PresetFusionGoal)
    # setupUi

    def retranslateUi(self, PresetFusionGoal):
        PresetFusionGoal.setWindowTitle(QCoreApplication.translate("PresetFusionGoal", u"Goal", None))
        self.description_label.setText(QCoreApplication.translate("PresetFusionGoal", u"<html><head/><body><p>In addition to preparing for battle with the SA-X, it is now necessary to collect the escaped Infant Metroids in order to reach the Operations Room. The minimum and maximum are limited to 0 and 20 Infant Metroids. You can choose to place more Metroids than required.</p></body></html>", None))
        self.placed_label.setText(QCoreApplication.translate("PresetFusionGoal", u"<html><head/><body><p>Controls how many Infant Metroids will be placed in the game.</p></body></html>", None))
        self.placed_slider_label.setText(QCoreApplication.translate("PresetFusionGoal", u"0", None))
        self.required_label.setText(QCoreApplication.translate("PresetFusionGoal", u"<html><head/><body><p>Controls how many Infant Metroids are required to beat the game.</p></body></html>", None))
        self.required_slider_label.setText(QCoreApplication.translate("PresetFusionGoal", u"0", None))
        self.placement_group.setTitle(QCoreApplication.translate("PresetFusionGoal", u"Placement", None))
        self.restrict_placement_radiobutton.setText(QCoreApplication.translate("PresetFusionGoal", u"Restricted Placement", None))
        self.restrict_placement_label.setText(QCoreApplication.translate("PresetFusionGoal", u"<html><head/><body><p>This option limits where Infant Metroids will be placed. There can only be as many Infant Metroids shuffled as there are preferred locations enabled.</p><p>In Multiworlds, Metroids are guaranteed to be in your World.</p></body></html>", None))
        self.prefer_bosses_check.setText(QCoreApplication.translate("PresetFusionGoal", u"Prefer Bosses. Adds 11 locations (Arachnus, Yakuza, Charge Core-X, Zazabi, Nettori, Wide Core-X, Serris, Nightmare, Varia Core-X, X-B.O.X., and Ridley)", None))
        self.free_placement_radiobutton.setText(QCoreApplication.translate("PresetFusionGoal", u"Free Placement", None))
        self.free_placement_label.setText(QCoreApplication.translate("PresetFusionGoal", u"Enables Infant Metroids to be placed anywhere. For Multiworlds, this means even other Worlds.", None))
    # retranslateUi

