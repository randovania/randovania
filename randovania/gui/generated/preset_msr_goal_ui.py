# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_msr_goal.ui'
##
## Created by: Qt User Interface Compiler version 6.6.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import *  # type: ignore
from PySide6.QtGui import *  # type: ignore
from PySide6.QtWidgets import *  # type: ignore

class Ui_PresetMSRGoal(object):
    def setupUi(self, PresetMSRGoal):
        if not PresetMSRGoal.objectName():
            PresetMSRGoal.setObjectName(u"PresetMSRGoal")
        PresetMSRGoal.resize(1196, 313)
        self.centralWidget = QWidget(PresetMSRGoal)
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
        self.dna_slider = QSlider(self.centralWidget)
        self.dna_slider.setObjectName(u"dna_slider")
        self.dna_slider.setMaximum(39)
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
        self.verticalLayout = QVBoxLayout(self.placement_group)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.restrict_placement_radiobutton = QRadioButton(self.placement_group)
        self.restrict_placement_radiobutton.setObjectName(u"restrict_placement_radiobutton")

        self.verticalLayout.addWidget(self.restrict_placement_radiobutton)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setSpacing(6)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(20, -1, -1, -1)
        self.restrict_placement_label = QLabel(self.placement_group)
        self.restrict_placement_label.setObjectName(u"restrict_placement_label")
        self.restrict_placement_label.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.restrict_placement_label)

        self.prefer_metroids_check = QCheckBox(self.placement_group)
        self.prefer_metroids_check.setObjectName(u"prefer_metroids_check")

        self.verticalLayout_2.addWidget(self.prefer_metroids_check)

        self.prefer_stronger_metroids_check = QCheckBox(self.placement_group)
        self.prefer_stronger_metroids_check.setObjectName(u"prefer_stronger_metroids_check")

        self.verticalLayout_2.addWidget(self.prefer_stronger_metroids_check)

        self.prefer_bosses_check = QCheckBox(self.placement_group)
        self.prefer_bosses_check.setObjectName(u"prefer_bosses_check")

        self.verticalLayout_2.addWidget(self.prefer_bosses_check)


        self.verticalLayout.addLayout(self.verticalLayout_2)

        self.free_placement_radiobutton = QRadioButton(self.placement_group)
        self.free_placement_radiobutton.setObjectName(u"free_placement_radiobutton")

        self.verticalLayout.addWidget(self.free_placement_radiobutton)

        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setSpacing(6)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(20, -1, -1, -1)
        self.free_placement_label = QLabel(self.placement_group)
        self.free_placement_label.setObjectName(u"free_placement_label")

        self.verticalLayout_3.addWidget(self.free_placement_label)


        self.verticalLayout.addLayout(self.verticalLayout_3)


        self.goal_layout.addWidget(self.placement_group)

        self.spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.goal_layout.addItem(self.spacer)

        PresetMSRGoal.setCentralWidget(self.centralWidget)

        self.retranslateUi(PresetMSRGoal)

        QMetaObject.connectSlotsByName(PresetMSRGoal)
    # setupUi

    def retranslateUi(self, PresetMSRGoal):
        PresetMSRGoal.setWindowTitle(QCoreApplication.translate("PresetMSRGoal", u"Goal", None))
        self.description_label.setText(QCoreApplication.translate("PresetMSRGoal", u"<html><head/><body><p>In addition to just collecting the Baby, it is now necessary to collect Metroid DNA in order to reach Ridley. The minimum and maximum are limited to 0 and 39 DNA respectively. You start with 39 DNA minus the shuffled amount.</p></body></html>", None))
        self.dna_slider_label.setText(QCoreApplication.translate("PresetMSRGoal", u"0", None))
        self.placement_group.setTitle(QCoreApplication.translate("PresetMSRGoal", u"Placement", None))
        self.restrict_placement_radiobutton.setText(QCoreApplication.translate("PresetMSRGoal", u"Restricted Placement", None))
        self.restrict_placement_label.setText(QCoreApplication.translate("PresetMSRGoal", u"<html><head/><body><p>The following options limit where Metroid DNA will be placed. There can only be as many DNA shuffled as there are preferred locations available. The first option adds 25 preferred locations, the second adds 14, and the third adds 4. In Multiworlds, DNA is guaranteed to be in your World.</p></body></html>", None))
        self.prefer_metroids_check.setText(QCoreApplication.translate("PresetMSRGoal", u"Prefer Standard Metroids (10 Alphas, 9 Gammas, 3 Zetas, 3 Omegas)", None))
        self.prefer_stronger_metroids_check.setText(QCoreApplication.translate("PresetMSRGoal", u"Prefer Stronger Metroids (7 Alpha+, 5 Gamma+, 1 Zeta+, 1 Omega+)", None))
        self.prefer_bosses_check.setText(QCoreApplication.translate("PresetMSRGoal", u"Prefer Bosses (Arachnus, Diggernaut Chase Reward, Diggernaut, Queen Metroid)", None))
        self.free_placement_radiobutton.setText(QCoreApplication.translate("PresetMSRGoal", u"Free Placement", None))
        self.free_placement_label.setText(QCoreApplication.translate("PresetMSRGoal", u"Enables DNA to be placed anywhere. For Multiworlds, this means even other Worlds.", None))
    # retranslateUi

