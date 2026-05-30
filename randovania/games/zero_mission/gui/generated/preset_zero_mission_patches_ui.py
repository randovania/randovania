# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_zero_mission_patches.ui'
##
## Created by: tools/uic_wrapper.py
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
from PySide6.QtWidgets import (QApplication, QGroupBox, QHBoxLayout, QLabel,
    QMainWindow, QScrollArea, QSizePolicy, QSpacerItem,
    QSpinBox, QVBoxLayout, QWidget)

class Ui_PresetMZMPatches(object):
    def setupUi(self, PresetMZMPatches):
        if not PresetMZMPatches.objectName():
            PresetMZMPatches.setObjectName(u"PresetMZMPatches")
        PresetMZMPatches.resize(725, 408)
        self.root_widget = QWidget(PresetMZMPatches)
        self.root_widget.setObjectName(u"root_widget")
        self.root_widget.setMaximumSize(QSize(16777215, 16777215))
        self.verticalLayout = QVBoxLayout(self.root_widget)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.scroll_area = QScrollArea(self.root_widget)
        self.scroll_area.setObjectName(u"scroll_area")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_contents = QWidget()
        self.scroll_contents.setObjectName(u"scroll_contents")
        self.scroll_contents.setGeometry(QRect(0, 0, 723, 406))
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scroll_contents.sizePolicy().hasHeightForWidth())
        self.scroll_contents.setSizePolicy(sizePolicy)
        self.scroll_layout = QVBoxLayout(self.scroll_contents)
        self.scroll_layout.setSpacing(6)
        self.scroll_layout.setContentsMargins(11, 11, 11, 11)
        self.scroll_layout.setObjectName(u"scroll_layout")
        self.scroll_layout.setContentsMargins(0, 2, 0, 0)
        self.top_spacer = QSpacerItem(20, 8, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.scroll_layout.addItem(self.top_spacer)

        self.energy_group = QGroupBox(self.scroll_contents)
        self.energy_group.setObjectName(u"energy_group")
        self.verticalLayout_2 = QVBoxLayout(self.energy_group)
        self.verticalLayout_2.setSpacing(6)
        self.verticalLayout_2.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.etank_description_label = QLabel(self.energy_group)
        self.etank_description_label.setObjectName(u"etank_description_label")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.etank_description_label.sizePolicy().hasHeightForWidth())
        self.etank_description_label.setSizePolicy(sizePolicy1)
        self.etank_description_label.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.etank_description_label)

        self.etank_layout = QHBoxLayout()
        self.etank_layout.setSpacing(6)
        self.etank_layout.setObjectName(u"etank_layout")
        self.etank_layout.setContentsMargins(-1, 0, -1, -1)
        self.etank_capacity_label = QLabel(self.energy_group)
        self.etank_capacity_label.setObjectName(u"etank_capacity_label")

        self.etank_layout.addWidget(self.etank_capacity_label)

        self.etank_capacity_spin_box = QSpinBox(self.energy_group)
        self.etank_capacity_spin_box.setObjectName(u"etank_capacity_spin_box")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.etank_capacity_spin_box.sizePolicy().hasHeightForWidth())
        self.etank_capacity_spin_box.setSizePolicy(sizePolicy2)
        self.etank_capacity_spin_box.setMinimum(1)
        self.etank_capacity_spin_box.setMaximum(1000)

        self.etank_layout.addWidget(self.etank_capacity_spin_box)


        self.verticalLayout_2.addLayout(self.etank_layout)


        self.scroll_layout.addWidget(self.energy_group)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.scroll_layout.addItem(self.verticalSpacer)

        self.scroll_area.setWidget(self.scroll_contents)

        self.verticalLayout.addWidget(self.scroll_area)

        PresetMZMPatches.setCentralWidget(self.root_widget)

        self.retranslateUi(PresetMZMPatches)

        QMetaObject.connectSlotsByName(PresetMZMPatches)
    # setupUi

    def retranslateUi(self, PresetMZMPatches):
        PresetMZMPatches.setWindowTitle(QCoreApplication.translate("PresetMZMPatches", u"Gameplay", None))
        self.energy_group.setTitle(QCoreApplication.translate("PresetMZMPatches", u"Energy", None))
        self.etank_description_label.setText(QCoreApplication.translate("PresetMZMPatches", u"Configure how much energy each Energy Tank you collect will provide. Your base energy is always this quantity, minus 1.\n"
"While logic will respect this value, only the original value (100) has been tested.", None))
        self.etank_capacity_label.setText(QCoreApplication.translate("PresetMZMPatches", u"Energy per tank:", None))
    # retranslateUi

