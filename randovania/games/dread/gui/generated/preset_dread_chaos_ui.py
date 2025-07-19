# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_dread_chaos.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QGroupBox, QLabel,
    QMainWindow, QScrollArea, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

class Ui_PresetDreadChaos(object):
    def setupUi(self, PresetDreadChaos):
        if not PresetDreadChaos.objectName():
            PresetDreadChaos.setObjectName(u"PresetDreadChaos")
        PresetDreadChaos.resize(503, 387)
        self.centralWidget = QWidget(PresetDreadChaos)
        self.centralWidget.setObjectName(u"centralWidget")
        self.centralWidget.setMaximumSize(QSize(16777215, 16777215))
        self.verticalLayout = QVBoxLayout(self.centralWidget)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.scroll_area = QScrollArea(self.centralWidget)
        self.scroll_area.setObjectName(u"scroll_area")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scroll_area.sizePolicy().hasHeightForWidth())
        self.scroll_area.setSizePolicy(sizePolicy)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_contents = QWidget()
        self.scroll_contents.setObjectName(u"scroll_contents")
        self.scroll_contents.setGeometry(QRect(0, 0, 501, 385))
        self.scroll_layout = QVBoxLayout(self.scroll_contents)
        self.scroll_layout.setSpacing(6)
        self.scroll_layout.setContentsMargins(11, 11, 11, 11)
        self.scroll_layout.setObjectName(u"scroll_layout")
        self.scroll_layout.setContentsMargins(6, 6, 6, 6)
        self.top_spacer = QSpacerItem(20, 8, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.scroll_layout.addItem(self.top_spacer)

        self.chaos_label = QLabel(self.scroll_contents)
        self.chaos_label.setObjectName(u"chaos_label")
        self.chaos_label.setWordWrap(True)

        self.scroll_layout.addWidget(self.chaos_label)

        self.misc_group = QGroupBox(self.scroll_contents)
        self.misc_group.setObjectName(u"misc_group")
        self.verticalLayout_7 = QVBoxLayout(self.misc_group)
        self.verticalLayout_7.setSpacing(6)
        self.verticalLayout_7.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.freesink_check = QCheckBox(self.misc_group)
        self.freesink_check.setObjectName(u"freesink_check")

        self.verticalLayout_7.addWidget(self.freesink_check)

        self.freesink_label = QLabel(self.misc_group)
        self.freesink_label.setObjectName(u"freesink_label")
        self.freesink_label.setWordWrap(True)

        self.verticalLayout_7.addWidget(self.freesink_label)


        self.scroll_layout.addWidget(self.misc_group)

        self.bottom_spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.scroll_layout.addItem(self.bottom_spacer)

        self.scroll_area.setWidget(self.scroll_contents)

        self.verticalLayout.addWidget(self.scroll_area)

        PresetDreadChaos.setCentralWidget(self.centralWidget)

        self.retranslateUi(PresetDreadChaos)

        QMetaObject.connectSlotsByName(PresetDreadChaos)
    # setupUi

    def retranslateUi(self, PresetDreadChaos):
        PresetDreadChaos.setWindowTitle(QCoreApplication.translate("PresetDreadChaos", u"Other", None))
        self.chaos_label.setText(QCoreApplication.translate("PresetDreadChaos", u"<html><head/><body><p>This page contains experimental settings which do not yet have (or will never have) logic support. </p></body></html>", None))
        self.misc_group.setTitle(QCoreApplication.translate("PresetDreadChaos", u"Miscellaneous", None))
        self.freesink_check.setText(QCoreApplication.translate("PresetDreadChaos", u"Enable Freesink", None))
        self.freesink_label.setText(QCoreApplication.translate("PresetDreadChaos", u"<html><head/><body><p>Usually, Samus will die if she is out of bounds, usually due to performing floor clips. When checked, this behavior is removed from the game and Samus can freely move out of bounds. </p></body></html>", None))
    # retranslateUi

