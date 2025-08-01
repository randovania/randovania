# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'scroll_label_dialog.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialog, QDialogButtonBox,
    QHBoxLayout, QLabel, QScrollArea, QSizePolicy,
    QVBoxLayout, QWidget)

class Ui_ScrollLabelDialog(object):
    def setupUi(self, ScrollLabelDialog):
        if not ScrollLabelDialog.objectName():
            ScrollLabelDialog.setObjectName(u"ScrollLabelDialog")
        ScrollLabelDialog.resize(518, 382)
        self.root_layout = QVBoxLayout(ScrollLabelDialog)
        self.root_layout.setSpacing(6)
        self.root_layout.setContentsMargins(11, 11, 11, 11)
        self.root_layout.setObjectName(u"root_layout")
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_area = QScrollArea(ScrollLabelDialog)
        self.scroll_area.setObjectName(u"scroll_area")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area_contents = QWidget()
        self.scroll_area_contents.setObjectName(u"scroll_area_contents")
        self.scroll_area_contents.setGeometry(QRect(0, 0, 516, 342))
        self.scroll_layout = QVBoxLayout(self.scroll_area_contents)
        self.scroll_layout.setSpacing(6)
        self.scroll_layout.setContentsMargins(11, 11, 11, 11)
        self.scroll_layout.setObjectName(u"scroll_layout")
        self.scroll_layout.setContentsMargins(2, 2, 2, 2)
        self.label = QLabel(self.scroll_area_contents)
        self.label.setObjectName(u"label")
        self.label.setMinimumSize(QSize(250, 0))
        self.label.setWordWrap(True)

        self.scroll_layout.addWidget(self.label)

        self.scroll_area.setWidget(self.scroll_area_contents)

        self.root_layout.addWidget(self.scroll_area)

        self.button_box_layout = QHBoxLayout()
        self.button_box_layout.setSpacing(6)
        self.button_box_layout.setObjectName(u"button_box_layout")
        self.button_box_layout.setContentsMargins(-1, -1, 6, 6)
        self.button_box = QDialogButtonBox(ScrollLabelDialog)
        self.button_box.setObjectName(u"button_box")
        self.button_box.setMinimumSize(QSize(500, 0))
        self.button_box.setStandardButtons(QDialogButtonBox.Ok)

        self.button_box_layout.addWidget(self.button_box)


        self.root_layout.addLayout(self.button_box_layout)


        self.retranslateUi(ScrollLabelDialog)

        QMetaObject.connectSlotsByName(ScrollLabelDialog)
    # setupUi

    def retranslateUi(self, ScrollLabelDialog):
        ScrollLabelDialog.setWindowTitle(QCoreApplication.translate("ScrollLabelDialog", u"Message box", None))
        self.label.setText(QCoreApplication.translate("ScrollLabelDialog", u"<html><head/><body><p><span style=\" font-weight:600;\">TextLabel</span></p><p><br/></p></body></html>", None))
    # retranslateUi

