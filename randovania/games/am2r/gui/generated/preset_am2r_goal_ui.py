# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_am2r_goal.ui'
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
    QLabel, QMainWindow, QRadioButton, QScrollArea,
    QSizePolicy, QSlider, QSpacerItem, QVBoxLayout,
    QWidget)

from randovania.gui.lib.scroll_protected import ScrollProtectedSlider

class Ui_PresetAM2RGoal(object):
    def setupUi(self, PresetAM2RGoal):
        if not PresetAM2RGoal.objectName():
            PresetAM2RGoal.setObjectName(u"PresetAM2RGoal")
        PresetAM2RGoal.resize(754, 664)
        self.centralWidget = QWidget(PresetAM2RGoal)
        self.centralWidget.setObjectName(u"centralWidget")
        self.centralWidget.setMaximumSize(QSize(16777215, 16777215))
        self.goal_layout = QVBoxLayout(self.centralWidget)
        self.goal_layout.setSpacing(6)
        self.goal_layout.setContentsMargins(11, 11, 11, 11)
        self.goal_layout.setObjectName(u"goal_layout")
        self.goal_layout.setContentsMargins(6, 6, 6, 6)
        self.scroll_area = QScrollArea(self.centralWidget)
        self.scroll_area.setObjectName(u"scroll_area")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area_contents = QWidget()
        self.scroll_area_contents.setObjectName(u"scroll_area_contents")
        self.scroll_area_contents.setGeometry(QRect(0, 0, 742, 652))
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scroll_area_contents.sizePolicy().hasHeightForWidth())
        self.scroll_area_contents.setSizePolicy(sizePolicy)
        self.scroll_area_layout = QVBoxLayout(self.scroll_area_contents)
        self.scroll_area_layout.setSpacing(6)
        self.scroll_area_layout.setContentsMargins(11, 11, 11, 11)
        self.scroll_area_layout.setObjectName(u"scroll_area_layout")
        self.scroll_area_layout.setContentsMargins(6, 6, 6, 6)
        self.description_label = QLabel(self.scroll_area_contents)
        self.description_label.setObjectName(u"description_label")
        self.description_label.setWordWrap(True)

        self.scroll_area_layout.addWidget(self.description_label)

        self.label_2 = QLabel(self.scroll_area_contents)
        self.label_2.setObjectName(u"label_2")

        self.scroll_area_layout.addWidget(self.label_2)

        self.placed_slider_layout = QHBoxLayout()
        self.placed_slider_layout.setSpacing(6)
        self.placed_slider_layout.setObjectName(u"placed_slider_layout")
        self.placed_slider_layout.setContentsMargins(6, 6, 6, 6)
        self.placed_slider = ScrollProtectedSlider(self.scroll_area_contents)
        self.placed_slider.setObjectName(u"placed_slider")
        self.placed_slider.setMaximum(46)
        self.placed_slider.setPageStep(2)
        self.placed_slider.setOrientation(Qt.Horizontal)
        self.placed_slider.setTickPosition(QSlider.TicksBelow)

        self.placed_slider_layout.addWidget(self.placed_slider)

        self.placed_slider_label = QLabel(self.scroll_area_contents)
        self.placed_slider_label.setObjectName(u"placed_slider_label")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.placed_slider_label.sizePolicy().hasHeightForWidth())
        self.placed_slider_label.setSizePolicy(sizePolicy1)
        self.placed_slider_label.setMinimumSize(QSize(0, 0))
        self.placed_slider_label.setAlignment(Qt.AlignCenter)

        self.placed_slider_layout.addWidget(self.placed_slider_label)


        self.scroll_area_layout.addLayout(self.placed_slider_layout)

        self.label = QLabel(self.scroll_area_contents)
        self.label.setObjectName(u"label")

        self.scroll_area_layout.addWidget(self.label)

        self.required_slider_layout = QHBoxLayout()
        self.required_slider_layout.setSpacing(6)
        self.required_slider_layout.setObjectName(u"required_slider_layout")
        self.required_slider_layout.setContentsMargins(6, 6, 6, 6)
        self.required_slider = ScrollProtectedSlider(self.scroll_area_contents)
        self.required_slider.setObjectName(u"required_slider")
        self.required_slider.setMaximum(46)
        self.required_slider.setPageStep(2)
        self.required_slider.setOrientation(Qt.Horizontal)
        self.required_slider.setTickPosition(QSlider.TicksBelow)
        self.required_slider.setTickInterval(0)

        self.required_slider_layout.addWidget(self.required_slider)

        self.required_slider_label = QLabel(self.scroll_area_contents)
        self.required_slider_label.setObjectName(u"required_slider_label")

        self.required_slider_layout.addWidget(self.required_slider_label)


        self.scroll_area_layout.addLayout(self.required_slider_layout)

        self.placement_group = QGroupBox(self.scroll_area_contents)
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

        self.prefer_metroids_check = QCheckBox(self.placement_group)
        self.prefer_metroids_check.setObjectName(u"prefer_metroids_check")

        self.verticalLayout_2.addWidget(self.prefer_metroids_check)

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


        self.scroll_area_layout.addWidget(self.placement_group)

        self.spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.scroll_area_layout.addItem(self.spacer)

        self.scroll_area.setWidget(self.scroll_area_contents)

        self.goal_layout.addWidget(self.scroll_area)

        PresetAM2RGoal.setCentralWidget(self.centralWidget)

        self.retranslateUi(PresetAM2RGoal)

        QMetaObject.connectSlotsByName(PresetAM2RGoal)
    # setupUi

    def retranslateUi(self, PresetAM2RGoal):
        PresetAM2RGoal.setWindowTitle(QCoreApplication.translate("PresetAM2RGoal", u"Goal", None))
        self.description_label.setText(QCoreApplication.translate("PresetAM2RGoal", u"<html><head/><body><p>In addition to just collecting the Baby, it's now necessary to collect Metroid DNA in order to reach the Queen. The minimum and maximum are limited to 0 and 46 DNA. You can choose to have more DNA in the Pool than what is required to collect.</p></body></html>", None))
        self.label_2.setText(QCoreApplication.translate("PresetAM2RGoal", u"Controls how much Metroid DNA is obtainable.", None))
        self.placed_slider_label.setText(QCoreApplication.translate("PresetAM2RGoal", u"0", None))
        self.label.setText(QCoreApplication.translate("PresetAM2RGoal", u"Controls how much Metroid DNA is required to be collected.", None))
        self.required_slider_label.setText(QCoreApplication.translate("PresetAM2RGoal", u"0", None))
        self.placement_group.setTitle(QCoreApplication.translate("PresetAM2RGoal", u"Placement", None))
        self.restrict_placement_radiobutton.setText(QCoreApplication.translate("PresetAM2RGoal", u"Restricted Placement", None))
        self.restrict_placement_label.setText(QCoreApplication.translate("PresetAM2RGoal", u"<html><head/><body><p>The following options limit where Metroid DNA will be placed. There can only be as many DNA shuffled as there are preferred locations enabled. The first option adds 46 preferred locations, the second 6. In Multiworlds, DNA is guaranteed to be in your World.</p></body></html>", None))
        self.prefer_metroids_check.setText(QCoreApplication.translate("PresetAM2RGoal", u"Prefer Metroids (23 Alphas, 15 Gammas, 4 Zetas, 4 Omegas)", None))
        self.prefer_bosses_check.setText(QCoreApplication.translate("PresetAM2RGoal", u"Prefer Bosses (Guardian, Arachnus, Torizo, The Tester, Serris and Genesis)", None))
        self.free_placement_radiobutton.setText(QCoreApplication.translate("PresetAM2RGoal", u"Free Placement", None))
        self.free_placement_label.setText(QCoreApplication.translate("PresetAM2RGoal", u"Enables DNA to be placed anywhere. For Multiworlds, this means even other Worlds.", None))
    # retranslateUi

