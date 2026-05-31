# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'prime2_opr_game_export_dialog.ui'
##
## Created by: tools/uic_wrapper.py
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QDialog, QFrame,
    QGridLayout, QLabel, QLineEdit, QPushButton,
    QSizePolicy, QWidget)

class Ui_EchoesOPRGameExportDialog(object):
    def setupUi(self, EchoesOPRGameExportDialog):
        if not EchoesOPRGameExportDialog.objectName():
            EchoesOPRGameExportDialog.setObjectName(u"EchoesOPRGameExportDialog")
        EchoesOPRGameExportDialog.resize(400, 300)
        self.gridLayout = QGridLayout(EchoesOPRGameExportDialog)
        self.gridLayout.setObjectName(u"gridLayout")
        self.input_file_button = QPushButton(EchoesOPRGameExportDialog)
        self.input_file_button.setObjectName(u"input_file_button")
        self.input_file_button.setMaximumSize(QSize(100, 16777215))

        self.gridLayout.addWidget(self.input_file_button, 2, 2, 1, 1)

        self.input_file_label = QLabel(EchoesOPRGameExportDialog)
        self.input_file_label.setObjectName(u"input_file_label")
        self.input_file_label.setMaximumSize(QSize(16777215, 20))

        self.gridLayout.addWidget(self.input_file_label, 1, 0, 1, 2)

        self.output_file_edit = QLineEdit(EchoesOPRGameExportDialog)
        self.output_file_edit.setObjectName(u"output_file_edit")

        self.gridLayout.addWidget(self.output_file_edit, 4, 0, 1, 2)

        self.output_file_label = QLabel(EchoesOPRGameExportDialog)
        self.output_file_label.setObjectName(u"output_file_label")
        self.output_file_label.setMaximumSize(QSize(16777215, 20))

        self.gridLayout.addWidget(self.output_file_label, 3, 0, 1, 2)

        self.input_file_edit = QLineEdit(EchoesOPRGameExportDialog)
        self.input_file_edit.setObjectName(u"input_file_edit")

        self.gridLayout.addWidget(self.input_file_edit, 2, 0, 1, 2)

        self.cancel_button = QPushButton(EchoesOPRGameExportDialog)
        self.cancel_button.setObjectName(u"cancel_button")

        self.gridLayout.addWidget(self.cancel_button, 6, 2, 1, 1)

        self.accept_button = QPushButton(EchoesOPRGameExportDialog)
        self.accept_button.setObjectName(u"accept_button")

        self.gridLayout.addWidget(self.accept_button, 6, 0, 1, 2)

        self.auto_save_spoiler_check = QCheckBox(EchoesOPRGameExportDialog)
        self.auto_save_spoiler_check.setObjectName(u"auto_save_spoiler_check")

        self.gridLayout.addWidget(self.auto_save_spoiler_check, 5, 0, 1, 2)

        self.output_file_button = QPushButton(EchoesOPRGameExportDialog)
        self.output_file_button.setObjectName(u"output_file_button")
        self.output_file_button.setMaximumSize(QSize(100, 16777215))

        self.gridLayout.addWidget(self.output_file_button, 4, 2, 1, 1)

        self.description_label = QLabel(EchoesOPRGameExportDialog)
        self.description_label.setObjectName(u"description_label")
        self.description_label.setFrameShape(QFrame.NoFrame)
        self.description_label.setWordWrap(True)

        self.gridLayout.addWidget(self.description_label, 0, 0, 1, 3)


        self.retranslateUi(EchoesOPRGameExportDialog)

        QMetaObject.connectSlotsByName(EchoesOPRGameExportDialog)
    # setupUi

    def retranslateUi(self, EchoesOPRGameExportDialog):
        EchoesOPRGameExportDialog.setWindowTitle(QCoreApplication.translate("EchoesOPRGameExportDialog", u"Dialog", None))
        self.input_file_button.setText(QCoreApplication.translate("EchoesOPRGameExportDialog", u"Select File", None))
        self.input_file_label.setText(QCoreApplication.translate("EchoesOPRGameExportDialog", u"Input File (Vanilla Gamecube ISO)", None))
        self.output_file_edit.setPlaceholderText(QCoreApplication.translate("EchoesOPRGameExportDialog", u"Path where to place randomized game", None))
        self.output_file_label.setText(QCoreApplication.translate("EchoesOPRGameExportDialog", u"Output File", None))
        self.input_file_edit.setPlaceholderText(QCoreApplication.translate("EchoesOPRGameExportDialog", u"Path to vanilla Gamecube ISO", None))
        self.cancel_button.setText(QCoreApplication.translate("EchoesOPRGameExportDialog", u"Cancel", None))
        self.accept_button.setText(QCoreApplication.translate("EchoesOPRGameExportDialog", u"Accept", None))
        self.auto_save_spoiler_check.setText(QCoreApplication.translate("EchoesOPRGameExportDialog", u"Include a spoiler log in the same directory", None))
        self.output_file_button.setText(QCoreApplication.translate("EchoesOPRGameExportDialog", u"Select File", None))
        self.description_label.setText(QCoreApplication.translate("EchoesOPRGameExportDialog", u"In order to create the randomized game, an ISO file of Metroid Prime 2: Echoes for the Nintendo Gamecube is necessary.", None))
    # retranslateUi

