# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_location_pool.ui'
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
from PySide6.QtWidgets import (QApplication, QMainWindow, QScrollArea, QSizePolicy,
    QVBoxLayout, QWidget)

class Ui_PresetLocationPool(object):
    def setupUi(self, PresetLocationPool):
        if not PresetLocationPool.objectName():
            PresetLocationPool.setObjectName(u"PresetLocationPool")
        PresetLocationPool.resize(505, 463)
        self.centralWidget = QWidget(PresetLocationPool)
        self.centralWidget.setObjectName(u"centralWidget")
        self.centralWidget.setMaximumSize(QSize(16777215, 16777215))
        self.verticalLayout = QVBoxLayout(self.centralWidget)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(2, 2, 2, 2)
        self.locations_scroll_area = QScrollArea(self.centralWidget)
        self.locations_scroll_area.setObjectName(u"locations_scroll_area")
        self.locations_scroll_area.setWidgetResizable(True)
        self.locations_scroll_area_contents = QWidget()
        self.locations_scroll_area_contents.setObjectName(u"locations_scroll_area_contents")
        self.locations_scroll_area_contents.setGeometry(QRect(0, 0, 499, 457))
        self.locations_scroll_area_layout = QVBoxLayout(self.locations_scroll_area_contents)
        self.locations_scroll_area_layout.setSpacing(6)
        self.locations_scroll_area_layout.setContentsMargins(11, 11, 11, 11)
        self.locations_scroll_area_layout.setObjectName(u"locations_scroll_area_layout")
        self.locations_scroll_area_layout.setContentsMargins(0, 0, 0, 0)
        self.locations_scroll_area.setWidget(self.locations_scroll_area_contents)

        self.verticalLayout.addWidget(self.locations_scroll_area)

        PresetLocationPool.setCentralWidget(self.centralWidget)

        self.retranslateUi(PresetLocationPool)

        QMetaObject.connectSlotsByName(PresetLocationPool)
    # setupUi

    def retranslateUi(self, PresetLocationPool):
        PresetLocationPool.setWindowTitle(QCoreApplication.translate("PresetLocationPool", u"Location Pool", None))
    # retranslateUi

