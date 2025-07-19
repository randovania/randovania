# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'async_race_admin_dialog.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialogButtonBox, QGridLayout,
    QHeaderView, QLabel, QSizePolicy, QTableView,
    QWidget)

class Ui_AsyncRaceAdminDialog(object):
    def setupUi(self, AsyncRaceAdminDialog):
        if not AsyncRaceAdminDialog.objectName():
            AsyncRaceAdminDialog.setObjectName(u"AsyncRaceAdminDialog")
        AsyncRaceAdminDialog.resize(625, 174)
        self.root_layout = QGridLayout(AsyncRaceAdminDialog)
        self.root_layout.setSpacing(6)
        self.root_layout.setContentsMargins(11, 11, 11, 11)
        self.root_layout.setObjectName(u"root_layout")
        self.button_box = QDialogButtonBox(AsyncRaceAdminDialog)
        self.button_box.setObjectName(u"button_box")
        self.button_box.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Save)

        self.root_layout.addWidget(self.button_box, 2, 0, 1, 1)

        self.table_view = QTableView(AsyncRaceAdminDialog)
        self.table_view.setObjectName(u"table_view")
        self.table_view.setAlternatingRowColors(True)

        self.root_layout.addWidget(self.table_view, 1, 0, 1, 1)

        self.label = QLabel(AsyncRaceAdminDialog)
        self.label.setObjectName(u"label")

        self.root_layout.addWidget(self.label, 0, 0, 1, 1)


        self.retranslateUi(AsyncRaceAdminDialog)

        QMetaObject.connectSlotsByName(AsyncRaceAdminDialog)
    # setupUi

    def retranslateUi(self, AsyncRaceAdminDialog):
        AsyncRaceAdminDialog.setWindowTitle(QCoreApplication.translate("AsyncRaceAdminDialog", u"Async Race Admin View", None))
        self.label.setText(QCoreApplication.translate("AsyncRaceAdminDialog", u"All times displayed are in your local time.", None))
    # retranslateUi

