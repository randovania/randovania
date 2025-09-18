# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'hotkeys_widget.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialogButtonBox, QHBoxLayout,
    QLabel, QLayout, QPushButton, QSizePolicy,
    QVBoxLayout, QWidget)

class Ui_HotkeyWidget(object):
    def setupUi(self, HotkeyWidget):
        if not HotkeyWidget.objectName():
            HotkeyWidget.setObjectName(u"HotkeyWidget")
        HotkeyWidget.resize(525, 213)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(HotkeyWidget.sizePolicy().hasHeightForWidth())
        HotkeyWidget.setSizePolicy(sizePolicy)
        HotkeyWidget.setMinimumSize(QSize(0, 0))
        HotkeyWidget.setMaximumSize(QSize(16777215, 16777215))
        self.verticalLayout = QVBoxLayout(HotkeyWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        self.title_label = QLabel(HotkeyWidget)
        self.title_label.setObjectName(u"title_label")
        self.title_label.setMaximumSize(QSize(5000, 50))
        self.title_label.setSizeIncrement(QSize(0, 0))
        self.title_label.setWordWrap(True)

        self.verticalLayout.addWidget(self.title_label)

        self.vertical_button_layout = QVBoxLayout()
        self.vertical_button_layout.setObjectName(u"vertical_button_layout")
        self.vertical_button_layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        self.start_finish_layout = QHBoxLayout()
        self.start_finish_layout.setObjectName(u"start_finish_layout")
        self.start_finish_label = QLabel(HotkeyWidget)
        self.start_finish_label.setObjectName(u"start_finish_label")

        self.start_finish_layout.addWidget(self.start_finish_label)

        self.start_finish_button = QPushButton(HotkeyWidget)
        self.start_finish_button.setObjectName(u"start_finish_button")

        self.start_finish_layout.addWidget(self.start_finish_button)


        self.vertical_button_layout.addLayout(self.start_finish_layout)

        self.pause_layout = QHBoxLayout()
        self.pause_layout.setObjectName(u"pause_layout")
        self.pause_label = QLabel(HotkeyWidget)
        self.pause_label.setObjectName(u"pause_label")

        self.pause_layout.addWidget(self.pause_label)

        self.pause_button = QPushButton(HotkeyWidget)
        self.pause_button.setObjectName(u"pause_button")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.pause_button.sizePolicy().hasHeightForWidth())
        self.pause_button.setSizePolicy(sizePolicy1)

        self.pause_layout.addWidget(self.pause_button)


        self.vertical_button_layout.addLayout(self.pause_layout)


        self.verticalLayout.addLayout(self.vertical_button_layout)

        self.dialog_buttons = QDialogButtonBox(HotkeyWidget)
        self.dialog_buttons.setObjectName(u"dialog_buttons")
        self.dialog_buttons.setOrientation(Qt.Orientation.Horizontal)
        self.dialog_buttons.setStandardButtons(QDialogButtonBox.StandardButton.Reset)
        self.dialog_buttons.setCenterButtons(True)

        self.verticalLayout.addWidget(self.dialog_buttons)


        self.retranslateUi(HotkeyWidget)

        QMetaObject.connectSlotsByName(HotkeyWidget)
    # setupUi

    def retranslateUi(self, HotkeyWidget):
        HotkeyWidget.setWindowTitle(QCoreApplication.translate("HotkeyWidget", u"Hotkeys", None))
        self.title_label.setText(QCoreApplication.translate("HotkeyWidget", u"<html><head/><body><p>Set your global hotkeys for the Async Race Rooms.<br>Please note that the Async Race Room window needs to stay open for the hotkeys to work.</p></body></html>", None))
        self.start_finish_label.setText(QCoreApplication.translate("HotkeyWidget", u"Start/Finish", None))
        self.start_finish_button.setText(QCoreApplication.translate("HotkeyWidget", u"Not Set", None))
        self.pause_label.setText(QCoreApplication.translate("HotkeyWidget", u"Pause/Unpause", None))
        self.pause_button.setText(QCoreApplication.translate("HotkeyWidget", u"Not Set", None))
    # retranslateUi

