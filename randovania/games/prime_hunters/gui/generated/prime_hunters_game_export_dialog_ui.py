# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'prime_hunters_game_export_dialog.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QDialog, QGridLayout,
    QLabel, QLineEdit, QPushButton, QSizePolicy,
    QWidget)

class Ui_HuntersGameExportDialog(object):
    def setupUi(self, HuntersGameExportDialog):
        if not HuntersGameExportDialog.objectName():
            HuntersGameExportDialog.setObjectName(u"HuntersGameExportDialog")
        HuntersGameExportDialog.resize(508, 309)
        self.gridLayout = QGridLayout(HuntersGameExportDialog)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setContentsMargins(11, 11, 11, 11)
        self.gridLayout.setObjectName(u"gridLayout")
        self.input_file_label = QLabel(HuntersGameExportDialog)
        self.input_file_label.setObjectName(u"input_file_label")

        self.gridLayout.addWidget(self.input_file_label, 1, 0, 1, 1)

        self.input_file_button = QPushButton(HuntersGameExportDialog)
        self.input_file_button.setObjectName(u"input_file_button")

        self.gridLayout.addWidget(self.input_file_button, 2, 1, 1, 1)

        self.output_file_edit = QLineEdit(HuntersGameExportDialog)
        self.output_file_edit.setObjectName(u"output_file_edit")

        self.gridLayout.addWidget(self.output_file_edit, 4, 0, 1, 1)

        self.cancel_button = QPushButton(HuntersGameExportDialog)
        self.cancel_button.setObjectName(u"cancel_button")

        self.gridLayout.addWidget(self.cancel_button, 6, 1, 1, 1)

        self.auto_save_spoiler_check = QCheckBox(HuntersGameExportDialog)
        self.auto_save_spoiler_check.setObjectName(u"auto_save_spoiler_check")

        self.gridLayout.addWidget(self.auto_save_spoiler_check, 5, 0, 1, 1)

        self.accept_button = QPushButton(HuntersGameExportDialog)
        self.accept_button.setObjectName(u"accept_button")

        self.gridLayout.addWidget(self.accept_button, 6, 0, 1, 1)

        self.output_file_button = QPushButton(HuntersGameExportDialog)
        self.output_file_button.setObjectName(u"output_file_button")

        self.gridLayout.addWidget(self.output_file_button, 4, 1, 1, 1)

        self.input_file_edit = QLineEdit(HuntersGameExportDialog)
        self.input_file_edit.setObjectName(u"input_file_edit")

        self.gridLayout.addWidget(self.input_file_edit, 2, 0, 1, 1)

        self.output_file_label = QLabel(HuntersGameExportDialog)
        self.output_file_label.setObjectName(u"output_file_label")

        self.gridLayout.addWidget(self.output_file_label, 3, 0, 1, 1)

        self.description_label = QLabel(HuntersGameExportDialog)
        self.description_label.setObjectName(u"description_label")
        self.description_label.setWordWrap(True)

        self.gridLayout.addWidget(self.description_label, 0, 0, 1, 2)


        self.retranslateUi(HuntersGameExportDialog)

        QMetaObject.connectSlotsByName(HuntersGameExportDialog)
    # setupUi

    def retranslateUi(self, HuntersGameExportDialog):
        HuntersGameExportDialog.setWindowTitle(QCoreApplication.translate("HuntersGameExportDialog", u"Game Patching", None))
        self.input_file_label.setText(QCoreApplication.translate("HuntersGameExportDialog", u"Input File (Vanilla Prime Hunters ROM)", None))
        self.input_file_button.setText(QCoreApplication.translate("HuntersGameExportDialog", u"Select File", None))
        self.output_file_edit.setPlaceholderText(QCoreApplication.translate("HuntersGameExportDialog", u"Path to where the randomized game will be outputted", None))
        self.cancel_button.setText(QCoreApplication.translate("HuntersGameExportDialog", u"Cancel", None))
        self.auto_save_spoiler_check.setText(QCoreApplication.translate("HuntersGameExportDialog", u"Include a spoiler log in the same directory", None))
        self.accept_button.setText(QCoreApplication.translate("HuntersGameExportDialog", u"Accept", None))
        self.output_file_button.setText(QCoreApplication.translate("HuntersGameExportDialog", u"Select File", None))
        self.input_file_edit.setText("")
        self.input_file_edit.setPlaceholderText(QCoreApplication.translate("HuntersGameExportDialog", u"Path to Hunters.nds", None))
        self.output_file_label.setText(QCoreApplication.translate("HuntersGameExportDialog", u"Output File", None))
        self.description_label.setText(QCoreApplication.translate("HuntersGameExportDialog", u"<html><head/><body><p>In order to create the randomized game, a ROM of Metroid Prime Hunters for the Nintendo DS is necessary.</p></body></html>", None))
    # retranslateUi

