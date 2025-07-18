# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_cs_hp.ui'
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
from PySide6.QtWidgets import (QApplication, QGridLayout, QGroupBox, QLabel,
    QMainWindow, QScrollArea, QSizePolicy, QSpacerItem,
    QSpinBox, QVBoxLayout, QWidget)

class Ui_PresetCSHP(object):
    def setupUi(self, PresetCSHP):
        if not PresetCSHP.objectName():
            PresetCSHP.setObjectName(u"PresetCSHP")
        PresetCSHP.resize(476, 628)
        self.centralWidget = QWidget(PresetCSHP)
        self.centralWidget.setObjectName(u"centralWidget")
        self.centralWidget.setMaximumSize(QSize(16777215, 16777215))
        self.main_layout = QVBoxLayout(self.centralWidget)
        self.main_layout.setSpacing(6)
        self.main_layout.setContentsMargins(11, 11, 11, 11)
        self.main_layout.setObjectName(u"main_layout")
        self.main_layout.setContentsMargins(6, 6, 6, 6)
        self.scroll_area = QScrollArea(self.centralWidget)
        self.scroll_area.setObjectName(u"scroll_area")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area_contents = QWidget()
        self.scroll_area_contents.setObjectName(u"scroll_area_contents")
        self.scroll_area_contents.setGeometry(QRect(0, 0, 464, 616))
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
        self.starting_hp_box = QGroupBox(self.scroll_area_contents)
        self.starting_hp_box.setObjectName(u"starting_hp_box")
        self.gridLayout_2 = QGridLayout(self.starting_hp_box)
        self.gridLayout_2.setSpacing(6)
        self.gridLayout_2.setContentsMargins(11, 11, 11, 11)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.starting_hp_spacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.gridLayout_2.addItem(self.starting_hp_spacer, 1, 0, 1, 2)

        self.starting_hp_spin_box = QSpinBox(self.starting_hp_box)
        self.starting_hp_spin_box.setObjectName(u"starting_hp_spin_box")
        self.starting_hp_spin_box.setMinimum(1)
        self.starting_hp_spin_box.setMaximum(55)
        self.starting_hp_spin_box.setValue(3)

        self.gridLayout_2.addWidget(self.starting_hp_spin_box, 2, 1, 1, 1)

        self.starting_hp_description = QLabel(self.starting_hp_box)
        self.starting_hp_description.setObjectName(u"starting_hp_description")
        self.starting_hp_description.setWordWrap(True)

        self.gridLayout_2.addWidget(self.starting_hp_description, 0, 0, 1, 2)

        self.starting_hp_label = QLabel(self.starting_hp_box)
        self.starting_hp_label.setObjectName(u"starting_hp_label")

        self.gridLayout_2.addWidget(self.starting_hp_label, 2, 0, 1, 1)


        self.scroll_area_layout.addWidget(self.starting_hp_box)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.scroll_area_layout.addItem(self.verticalSpacer)

        self.scroll_area.setWidget(self.scroll_area_contents)

        self.main_layout.addWidget(self.scroll_area)

        PresetCSHP.setCentralWidget(self.centralWidget)

        self.retranslateUi(PresetCSHP)

        QMetaObject.connectSlotsByName(PresetCSHP)
    # setupUi

    def retranslateUi(self, PresetCSHP):
        PresetCSHP.setWindowTitle(QCoreApplication.translate("PresetCSHP", u"HP", None))
        self.starting_hp_box.setTitle(QCoreApplication.translate("PresetCSHP", u"Starting HP", None))
        self.starting_hp_spin_box.setSuffix(QCoreApplication.translate("PresetCSHP", u"  HP", None))
        self.starting_hp_description.setText(QCoreApplication.translate("PresetCSHP", u"Configure how much HP you start the game with.", None))
        self.starting_hp_label.setText(QCoreApplication.translate("PresetCSHP", u"Starting HP", None))
    # retranslateUi

