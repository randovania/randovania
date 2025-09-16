# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_starting_area.ui'
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
from PySide6.QtWidgets import (QApplication, QGridLayout, QHBoxLayout, QLabel,
    QMainWindow, QScrollArea, QSizePolicy, QVBoxLayout,
    QWidget)

class Ui_PresetStartingArea(object):
    def setupUi(self, PresetStartingArea):
        if not PresetStartingArea.objectName():
            PresetStartingArea.setObjectName(u"PresetStartingArea")
        PresetStartingArea.resize(505, 463)
        self.centralWidget = QWidget(PresetStartingArea)
        self.centralWidget.setObjectName(u"centralWidget")
        self.centralWidget.setMaximumSize(QSize(16777215, 16777215))
        self.starting_area_layout = QVBoxLayout(self.centralWidget)
        self.starting_area_layout.setSpacing(6)
        self.starting_area_layout.setContentsMargins(11, 11, 11, 11)
        self.starting_area_layout.setObjectName(u"starting_area_layout")
        self.starting_area_layout.setContentsMargins(4, 6, 4, 0)
        self.startingarea_description = QLabel(self.centralWidget)
        self.startingarea_description.setObjectName(u"startingarea_description")
        self.startingarea_description.setTextFormat(Qt.AutoText)
        self.startingarea_description.setWordWrap(True)

        self.starting_area_layout.addWidget(self.startingarea_description)

        self.starting_area_quick_fill_layout = QHBoxLayout()
        self.starting_area_quick_fill_layout.setSpacing(6)
        self.starting_area_quick_fill_layout.setObjectName(u"starting_area_quick_fill_layout")
        self.starting_area_quick_fill_label = QLabel(self.centralWidget)
        self.starting_area_quick_fill_label.setObjectName(u"starting_area_quick_fill_label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.starting_area_quick_fill_label.sizePolicy().hasHeightForWidth())
        self.starting_area_quick_fill_label.setSizePolicy(sizePolicy)

        self.starting_area_quick_fill_layout.addWidget(self.starting_area_quick_fill_label)


        self.starting_area_layout.addLayout(self.starting_area_quick_fill_layout)

        self.starting_locations_area = QScrollArea(self.centralWidget)
        self.starting_locations_area.setObjectName(u"starting_locations_area")
        self.starting_locations_area.setWidgetResizable(True)
        self.starting_locations_contents = QWidget()
        self.starting_locations_contents.setObjectName(u"starting_locations_contents")
        self.starting_locations_contents.setGeometry(QRect(0, 0, 495, 349))
        self.starting_locations_layout = QGridLayout(self.starting_locations_contents)
        self.starting_locations_layout.setSpacing(6)
        self.starting_locations_layout.setContentsMargins(11, 11, 11, 11)
        self.starting_locations_layout.setObjectName(u"starting_locations_layout")
        self.starting_locations_layout.setContentsMargins(4, 4, 4, 4)
        self.starting_locations_area.setWidget(self.starting_locations_contents)

        self.starting_area_layout.addWidget(self.starting_locations_area)

        PresetStartingArea.setCentralWidget(self.centralWidget)

        self.retranslateUi(PresetStartingArea)

        QMetaObject.connectSlotsByName(PresetStartingArea)
    # setupUi

    def retranslateUi(self, PresetStartingArea):
        PresetStartingArea.setWindowTitle(QCoreApplication.translate("PresetStartingArea", u"Starting Area", None))
        self.startingarea_description.setText(QCoreApplication.translate("PresetStartingArea", u"<html><head/><body><p>The area where the game starts at can be customized, being selected randomly from a list.</p><p>For ease of use, you can select some pre-defined list of locations. They are:<br/>{quick_fill_text}</p><p><span style=\" font-weight:600;\">WARNING</span>: depending on the starting items that are configured, it may be impossible to start at the chosen place. In that case, the generation will fail.</p></body></html>", None))
        self.starting_area_quick_fill_label.setText(QCoreApplication.translate("PresetStartingArea", u"Quick Fill with:", None))
    # retranslateUi

