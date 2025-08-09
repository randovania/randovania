# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'permalink_dialog.ui'
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

class Ui_PermalinkDialog(object):
    def setupUi(self, PermalinkDialog):
        if not PermalinkDialog.objectName():
            PermalinkDialog.setObjectName(u"PermalinkDialog")
        PermalinkDialog.resize(539, 117)
        self.gridLayout = QGridLayout(PermalinkDialog)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setContentsMargins(11, 11, 11, 11)
        self.gridLayout.setObjectName(u"gridLayout")
        self.accept_button = QPushButton(PermalinkDialog)
        self.accept_button.setObjectName(u"accept_button")

        self.gridLayout.addWidget(self.accept_button, 6, 0, 1, 1)

        self.permalink_edit = QLineEdit(PermalinkDialog)
        self.permalink_edit.setObjectName(u"permalink_edit")

        self.gridLayout.addWidget(self.permalink_edit, 4, 0, 1, 3)

        self.cancel_button = QPushButton(PermalinkDialog)
        self.cancel_button.setObjectName(u"cancel_button")

        self.gridLayout.addWidget(self.cancel_button, 6, 2, 1, 1)

        self.paste_button = QPushButton(PermalinkDialog)
        self.paste_button.setObjectName(u"paste_button")

        self.gridLayout.addWidget(self.paste_button, 1, 2, 1, 1)

        self.description_label = QLabel(PermalinkDialog)
        self.description_label.setObjectName(u"description_label")

        self.gridLayout.addWidget(self.description_label, 1, 0, 1, 2)

        self.import_error_label = QLabel(PermalinkDialog)
        self.import_error_label.setObjectName(u"import_error_label")
        self.import_error_label.setWordWrap(True)

        self.gridLayout.addWidget(self.import_error_label, 5, 0, 1, 3)


        self.retranslateUi(PermalinkDialog)

        QMetaObject.connectSlotsByName(PermalinkDialog)
    # setupUi

    def retranslateUi(self, PermalinkDialog):
        PermalinkDialog.setWindowTitle(QCoreApplication.translate("PermalinkDialog", u"Import permalink", None))
        self.accept_button.setText(QCoreApplication.translate("PermalinkDialog", u"Accept", None))
        self.permalink_edit.setPlaceholderText(QCoreApplication.translate("PermalinkDialog", u"Permalink", None))
        self.cancel_button.setText(QCoreApplication.translate("PermalinkDialog", u"Cancel", None))
        self.paste_button.setText(QCoreApplication.translate("PermalinkDialog", u"Paste", None))
        self.description_label.setText(QCoreApplication.translate("PermalinkDialog", u"<html><head/><body><p>Import a permalink that was shared by someone else.</p></body></html>", None))
        self.import_error_label.setText("")
    # retranslateUi

