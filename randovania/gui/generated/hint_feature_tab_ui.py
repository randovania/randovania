# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'hint_feature_tab.ui'
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
from PySide6.QtWidgets import (QApplication, QLabel, QScrollArea, QSizePolicy,
    QVBoxLayout, QWidget)

class Ui_HintFeatureTab(object):
    def setupUi(self, HintFeatureTab):
        if not HintFeatureTab.objectName():
            HintFeatureTab.setObjectName(u"HintFeatureTab")
        HintFeatureTab.resize(400, 300)
        self.verticalLayout_2 = QVBoxLayout(HintFeatureTab)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.description_label = QLabel(HintFeatureTab)
        self.description_label.setObjectName(u"description_label")
        self.description_label.setTextFormat(Qt.MarkdownText)
        self.description_label.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.description_label)

        self.scroll_area = QScrollArea(HintFeatureTab)
        self.scroll_area.setObjectName(u"scroll_area")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area_contents = QWidget()
        self.scroll_area_contents.setObjectName(u"scroll_area_contents")
        self.scroll_area_contents.setGeometry(QRect(0, 0, 380, 226))
        self.verticalLayout_3 = QVBoxLayout(self.scroll_area_contents)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.scroll_area.setWidget(self.scroll_area_contents)

        self.verticalLayout_2.addWidget(self.scroll_area)


        self.retranslateUi(HintFeatureTab)

        QMetaObject.connectSlotsByName(HintFeatureTab)
    # setupUi

    def retranslateUi(self, HintFeatureTab):
        HintFeatureTab.setWindowTitle(QCoreApplication.translate("HintFeatureTab", u"Form", None))
        self.description_label.setText(QCoreApplication.translate("HintFeatureTab", u"When a pickup is referenced in a hint, the hint may refer to it using a Feature of varying precision. The following is a list of which pickups a given Feature may refer to:", None))
    # retranslateUi

