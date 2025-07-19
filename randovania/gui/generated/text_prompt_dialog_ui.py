# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'text_prompt_dialog.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QGridLayout, QLabel,
    QLineEdit, QPushButton, QSizePolicy, QWidget)

class Ui_TextPromptDialog(object):
    def setupUi(self, TextPromptDialog):
        if not TextPromptDialog.objectName():
            TextPromptDialog.setObjectName(u"TextPromptDialog")
        TextPromptDialog.resize(539, 117)
        self.gridLayout = QGridLayout(TextPromptDialog)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setContentsMargins(11, 11, 11, 11)
        self.gridLayout.setObjectName(u"gridLayout")
        self.accept_button = QPushButton(TextPromptDialog)
        self.accept_button.setObjectName(u"accept_button")

        self.gridLayout.addWidget(self.accept_button, 6, 0, 1, 1)

        self.prompt_edit = QLineEdit(TextPromptDialog)
        self.prompt_edit.setObjectName(u"prompt_edit")

        self.gridLayout.addWidget(self.prompt_edit, 4, 0, 1, 3)

        self.cancel_button = QPushButton(TextPromptDialog)
        self.cancel_button.setObjectName(u"cancel_button")

        self.gridLayout.addWidget(self.cancel_button, 6, 2, 1, 1)

        self.error_label = QLabel(TextPromptDialog)
        self.error_label.setObjectName(u"error_label")
        self.error_label.setWordWrap(True)

        self.gridLayout.addWidget(self.error_label, 5, 0, 1, 3)

        self.description_label = QLabel(TextPromptDialog)
        self.description_label.setObjectName(u"description_label")

        self.gridLayout.addWidget(self.description_label, 1, 0, 1, 3)


        self.retranslateUi(TextPromptDialog)

        QMetaObject.connectSlotsByName(TextPromptDialog)
    # setupUi

    def retranslateUi(self, TextPromptDialog):
        TextPromptDialog.setWindowTitle(QCoreApplication.translate("TextPromptDialog", u"Import permalink", None))
        self.accept_button.setText(QCoreApplication.translate("TextPromptDialog", u"Accept", None))
        self.cancel_button.setText(QCoreApplication.translate("TextPromptDialog", u"Cancel", None))
        self.error_label.setText("")
        self.description_label.setText(QCoreApplication.translate("TextPromptDialog", u"<html><head/><body><p>&lt;placeholder&gt;</p></body></html>", None))
    # retranslateUi

