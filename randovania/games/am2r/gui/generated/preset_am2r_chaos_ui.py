# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_am2r_chaos.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QGroupBox, QHBoxLayout,
    QLabel, QMainWindow, QScrollArea, QSizePolicy,
    QSlider, QSpacerItem, QSpinBox, QVBoxLayout,
    QWidget)

from randovania.gui.lib.scroll_protected import ScrollProtectedSlider

class Ui_PresetAM2RChaos(object):
    def setupUi(self, PresetAM2RChaos):
        if not PresetAM2RChaos.objectName():
            PresetAM2RChaos.setObjectName(u"PresetAM2RChaos")
        PresetAM2RChaos.resize(518, 687)
        self.centralWidget = QWidget(PresetAM2RChaos)
        self.centralWidget.setObjectName(u"centralWidget")
        self.centralWidget.setMaximumSize(QSize(16777215, 16777215))
        self.verticalLayout = QVBoxLayout(self.centralWidget)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(6, 6, 6, 6)
        self.scroll_area = QScrollArea(self.centralWidget)
        self.scroll_area.setObjectName(u"scroll_area")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_contents = QWidget()
        self.scroll_contents.setObjectName(u"scroll_contents")
        self.scroll_contents.setGeometry(QRect(0, 0, 506, 675))
        self.scroll_layout = QVBoxLayout(self.scroll_contents)
        self.scroll_layout.setSpacing(6)
        self.scroll_layout.setContentsMargins(11, 11, 11, 11)
        self.scroll_layout.setObjectName(u"scroll_layout")
        self.scroll_layout.setContentsMargins(6, 6, 6, 6)
        self.chaos_label = QLabel(self.scroll_contents)
        self.chaos_label.setObjectName(u"chaos_label")
        self.chaos_label.setWordWrap(True)

        self.scroll_layout.addWidget(self.chaos_label)

        self.shuffle_item_pos_group = QGroupBox(self.scroll_contents)
        self.shuffle_item_pos_group.setObjectName(u"shuffle_item_pos_group")
        self.verticalLayout_4 = QVBoxLayout(self.shuffle_item_pos_group)
        self.verticalLayout_4.setSpacing(6)
        self.verticalLayout_4.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.darkness_label = QLabel(self.shuffle_item_pos_group)
        self.darkness_label.setObjectName(u"darkness_label")
        self.darkness_label.setWordWrap(True)

        self.verticalLayout_4.addWidget(self.darkness_label)

        self.darkness_layout = QHBoxLayout()
        self.darkness_layout.setSpacing(6)
        self.darkness_layout.setObjectName(u"darkness_layout")
        self.darkness_layout.setContentsMargins(6, 6, 6, 6)
        self.darkness_slider = ScrollProtectedSlider(self.shuffle_item_pos_group)
        self.darkness_slider.setObjectName(u"darkness_slider")
        self.darkness_slider.setMaximum(1000)
        self.darkness_slider.setPageStep(2)
        self.darkness_slider.setOrientation(Qt.Horizontal)
        self.darkness_slider.setTickPosition(QSlider.TicksBelow)

        self.darkness_layout.addWidget(self.darkness_slider)

        self.darkness_slider_label = QLabel(self.shuffle_item_pos_group)
        self.darkness_slider_label.setObjectName(u"darkness_slider_label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.darkness_slider_label.sizePolicy().hasHeightForWidth())
        self.darkness_slider_label.setSizePolicy(sizePolicy)
        self.darkness_slider_label.setMinimumSize(QSize(20, 0))
        self.darkness_slider_label.setAlignment(Qt.AlignCenter)

        self.darkness_layout.addWidget(self.darkness_slider_label)


        self.verticalLayout_4.addLayout(self.darkness_layout)

        self.darkness_restriction_layout = QHBoxLayout()
        self.darkness_restriction_layout.setSpacing(6)
        self.darkness_restriction_layout.setObjectName(u"darkness_restriction_layout")
        self.darkness_restriction_layout.setContentsMargins(6, 6, 6, 6)
        self.darkness_min_label = QLabel(self.shuffle_item_pos_group)
        self.darkness_min_label.setObjectName(u"darkness_min_label")

        self.darkness_restriction_layout.addWidget(self.darkness_min_label)

        self.darkness_min_spin = QSpinBox(self.shuffle_item_pos_group)
        self.darkness_min_spin.setObjectName(u"darkness_min_spin")
        self.darkness_min_spin.setMaximum(4)

        self.darkness_restriction_layout.addWidget(self.darkness_min_spin)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.darkness_restriction_layout.addItem(self.horizontalSpacer)

        self.darkness_max_label = QLabel(self.shuffle_item_pos_group)
        self.darkness_max_label.setObjectName(u"darkness_max_label")

        self.darkness_restriction_layout.addWidget(self.darkness_max_label)

        self.darkness_max_spin = QSpinBox(self.shuffle_item_pos_group)
        self.darkness_max_spin.setObjectName(u"darkness_max_spin")
        self.darkness_max_spin.setMaximum(4)

        self.darkness_restriction_layout.addWidget(self.darkness_max_spin)


        self.verticalLayout_4.addLayout(self.darkness_restriction_layout)

        self.verticalSpacer_2 = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_4.addItem(self.verticalSpacer_2)

        self.line = QFrame(self.shuffle_item_pos_group)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_4.addWidget(self.line)

        self.verticalSpacer_3 = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_4.addItem(self.verticalSpacer_3)

        self.submerged_label = QLabel(self.shuffle_item_pos_group)
        self.submerged_label.setObjectName(u"submerged_label")
        self.submerged_label.setWordWrap(True)

        self.verticalLayout_4.addWidget(self.submerged_label)

        self.submerged_water_slider_layout = QHBoxLayout()
        self.submerged_water_slider_layout.setSpacing(6)
        self.submerged_water_slider_layout.setObjectName(u"submerged_water_slider_layout")
        self.submerged_water_slider_layout.setContentsMargins(6, 6, 6, 6)
        self.submerged_water_label = QLabel(self.shuffle_item_pos_group)
        self.submerged_water_label.setObjectName(u"submerged_water_label")

        self.submerged_water_slider_layout.addWidget(self.submerged_water_label)

        self.submerged_water_slider = ScrollProtectedSlider(self.shuffle_item_pos_group)
        self.submerged_water_slider.setObjectName(u"submerged_water_slider")
        self.submerged_water_slider.setMaximum(1000)
        self.submerged_water_slider.setPageStep(2)
        self.submerged_water_slider.setOrientation(Qt.Horizontal)
        self.submerged_water_slider.setTickPosition(QSlider.TicksBelow)

        self.submerged_water_slider_layout.addWidget(self.submerged_water_slider)

        self.submerged_water_slider_label = QLabel(self.shuffle_item_pos_group)
        self.submerged_water_slider_label.setObjectName(u"submerged_water_slider_label")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.submerged_water_slider_label.sizePolicy().hasHeightForWidth())
        self.submerged_water_slider_label.setSizePolicy(sizePolicy1)
        self.submerged_water_slider_label.setMinimumSize(QSize(20, 0))
        self.submerged_water_slider_label.setAlignment(Qt.AlignCenter)

        self.submerged_water_slider_layout.addWidget(self.submerged_water_slider_label)


        self.verticalLayout_4.addLayout(self.submerged_water_slider_layout)

        self.submerged_lava_slider_layout = QHBoxLayout()
        self.submerged_lava_slider_layout.setSpacing(6)
        self.submerged_lava_slider_layout.setObjectName(u"submerged_lava_slider_layout")
        self.submerged_lava_slider_layout.setContentsMargins(6, 6, 6, 6)
        self.submerged_lava_label = QLabel(self.shuffle_item_pos_group)
        self.submerged_lava_label.setObjectName(u"submerged_lava_label")

        self.submerged_lava_slider_layout.addWidget(self.submerged_lava_label)

        self.submerged_lava_slider = ScrollProtectedSlider(self.shuffle_item_pos_group)
        self.submerged_lava_slider.setObjectName(u"submerged_lava_slider")
        self.submerged_lava_slider.setMaximum(1000)
        self.submerged_lava_slider.setPageStep(2)
        self.submerged_lava_slider.setOrientation(Qt.Horizontal)
        self.submerged_lava_slider.setTickPosition(QSlider.TicksBelow)

        self.submerged_lava_slider_layout.addWidget(self.submerged_lava_slider)

        self.submerged_lava_slider_label = QLabel(self.shuffle_item_pos_group)
        self.submerged_lava_slider_label.setObjectName(u"submerged_lava_slider_label")

        self.submerged_lava_slider_layout.addWidget(self.submerged_lava_slider_label)


        self.verticalLayout_4.addLayout(self.submerged_lava_slider_layout)


        self.scroll_layout.addWidget(self.shuffle_item_pos_group)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.scroll_layout.addItem(self.verticalSpacer)

        self.scroll_area.setWidget(self.scroll_contents)

        self.verticalLayout.addWidget(self.scroll_area)

        PresetAM2RChaos.setCentralWidget(self.centralWidget)

        self.retranslateUi(PresetAM2RChaos)

        QMetaObject.connectSlotsByName(PresetAM2RChaos)
    # setupUi

    def retranslateUi(self, PresetAM2RChaos):
        PresetAM2RChaos.setWindowTitle(QCoreApplication.translate("PresetAM2RChaos", u"Other", None))
        self.chaos_label.setText(QCoreApplication.translate("PresetAM2RChaos", u"<html><head/><body><p>This page contains experimental settings which do not have logic support. This means that games generated with anything other than this tab's default settings may result in incompletable seeds.</p></body></html>", None))
        self.shuffle_item_pos_group.setTitle(QCoreApplication.translate("PresetAM2RChaos", u"Room Attributes", None))
        self.darkness_label.setText(QCoreApplication.translate("PresetAM2RChaos", u"<html><head/><body><p>Darkness Probability: Probability that any room has a custom darkness value compared to vanilla. Boxes below control minimum and maximum darkness values with 0 being brightest and 4 being darkest.</p></body></html>", None))
        self.darkness_slider_label.setText(QCoreApplication.translate("PresetAM2RChaos", u"0", None))
        self.darkness_min_label.setText(QCoreApplication.translate("PresetAM2RChaos", u"Minimum Darkness: ", None))
        self.darkness_max_label.setText(QCoreApplication.translate("PresetAM2RChaos", u"Maximum Darkness: ", None))
        self.submerged_label.setText(QCoreApplication.translate("PresetAM2RChaos", u"<html><head/><body><p>Submerged Probability: Probability that any room is fully submerged in either water or lava. Rooms which already contain liquids will have their liquid state re-rolled.<br/>Completely ignores underwater movement logic, as well as logic for damage boosting through lava.</p></body></html>", None))
        self.submerged_water_label.setText(QCoreApplication.translate("PresetAM2RChaos", u"Water Probability:", None))
        self.submerged_water_slider_label.setText(QCoreApplication.translate("PresetAM2RChaos", u"0", None))
        self.submerged_lava_label.setText(QCoreApplication.translate("PresetAM2RChaos", u"Lava Probability:", None))
        self.submerged_lava_slider_label.setText(QCoreApplication.translate("PresetAM2RChaos", u"0", None))
    # retranslateUi

