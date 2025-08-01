# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'connections_editor.ui'
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
    QGridLayout, QScrollArea, QSizePolicy, QVBoxLayout,
    QWidget)

class Ui_ConnectionEditor(object):
    def setupUi(self, ConnectionEditor):
        if not ConnectionEditor.objectName():
            ConnectionEditor.setObjectName(u"ConnectionEditor")
        ConnectionEditor.resize(794, 393)
        ConnectionEditor.setMinimumSize(QSize(600, 0))
        self.gridLayout_2 = QGridLayout(ConnectionEditor)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.visualizer_scroll = QScrollArea(ConnectionEditor)
        self.visualizer_scroll.setObjectName(u"visualizer_scroll")
        self.visualizer_scroll.setWidgetResizable(True)
        self.visualizer_contents = QWidget()
        self.visualizer_contents.setObjectName(u"visualizer_contents")
        self.visualizer_contents.setGeometry(QRect(0, 0, 774, 345))
        self.contents_layout = QVBoxLayout(self.visualizer_contents)
        self.contents_layout.setObjectName(u"contents_layout")
        self.visualizer_scroll.setWidget(self.visualizer_contents)

        self.gridLayout_2.addWidget(self.visualizer_scroll, 0, 0, 1, 1)

        self.button_box = QDialogButtonBox(ConnectionEditor)
        self.button_box.setObjectName(u"button_box")
        self.button_box.setOrientation(Qt.Horizontal)
        self.button_box.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.gridLayout_2.addWidget(self.button_box, 1, 0, 1, 1)


        self.retranslateUi(ConnectionEditor)
        self.button_box.accepted.connect(ConnectionEditor.accept)
        self.button_box.rejected.connect(ConnectionEditor.reject)

        QMetaObject.connectSlotsByName(ConnectionEditor)
    # setupUi

    def retranslateUi(self, ConnectionEditor):
        ConnectionEditor.setWindowTitle(QCoreApplication.translate("ConnectionEditor", u"Connection Editor", None))
    # retranslateUi

