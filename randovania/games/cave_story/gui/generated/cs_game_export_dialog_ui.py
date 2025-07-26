# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'cs_game_export_dialog.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QDialog, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QRadioButton, QSizePolicy, QWidget)

class Ui_CSGameExportDialog(object):
    def setupUi(self, CSGameExportDialog):
        if not CSGameExportDialog.objectName():
            CSGameExportDialog.setObjectName(u"CSGameExportDialog")
        CSGameExportDialog.resize(508, 270)
        self.gridLayout = QGridLayout(CSGameExportDialog)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setContentsMargins(11, 11, 11, 11)
        self.gridLayout.setObjectName(u"gridLayout")
        self.output_file_button = QPushButton(CSGameExportDialog)
        self.output_file_button.setObjectName(u"output_file_button")
        self.output_file_button.setMaximumSize(QSize(100, 16777215))

        self.gridLayout.addWidget(self.output_file_button, 4, 2, 1, 1)

        self.auto_save_spoiler_check = QCheckBox(CSGameExportDialog)
        self.auto_save_spoiler_check.setObjectName(u"auto_save_spoiler_check")

        self.gridLayout.addWidget(self.auto_save_spoiler_check, 6, 0, 1, 1)

        self.cancel_button = QPushButton(CSGameExportDialog)
        self.cancel_button.setObjectName(u"cancel_button")

        self.gridLayout.addWidget(self.cancel_button, 7, 2, 1, 1)

        self.output_file_label = QLabel(CSGameExportDialog)
        self.output_file_label.setObjectName(u"output_file_label")
        self.output_file_label.setMaximumSize(QSize(16777215, 20))

        self.gridLayout.addWidget(self.output_file_label, 3, 0, 1, 2)

        self.output_file_edit = QLineEdit(CSGameExportDialog)
        self.output_file_edit.setObjectName(u"output_file_edit")

        self.gridLayout.addWidget(self.output_file_edit, 4, 0, 1, 2)

        self.accept_button = QPushButton(CSGameExportDialog)
        self.accept_button.setObjectName(u"accept_button")

        self.gridLayout.addWidget(self.accept_button, 7, 0, 1, 1)

        self.select_label = QLabel(CSGameExportDialog)
        self.select_label.setObjectName(u"select_label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.select_label.sizePolicy().hasHeightForWidth())
        self.select_label.setSizePolicy(sizePolicy)
        self.select_label.setMaximumSize(QSize(16777215, 20))
        self.select_label.setBaseSize(QSize(0, 70))
        self.select_label.setWordWrap(True)

        self.gridLayout.addWidget(self.select_label, 0, 0, 1, 2)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.freeware_radio = QRadioButton(CSGameExportDialog)
        self.freeware_radio.setObjectName(u"freeware_radio")
        self.freeware_radio.setMaximumSize(QSize(16777215, 20))

        self.horizontalLayout.addWidget(self.freeware_radio)

        self.tweaked_radio = QRadioButton(CSGameExportDialog)
        self.tweaked_radio.setObjectName(u"tweaked_radio")
        self.tweaked_radio.setMaximumSize(QSize(16777215, 20))

        self.horizontalLayout.addWidget(self.tweaked_radio)


        self.gridLayout.addLayout(self.horizontalLayout, 1, 0, 1, 3)

        self.description_label = QLabel(CSGameExportDialog)
        self.description_label.setObjectName(u"description_label")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.description_label.sizePolicy().hasHeightForWidth())
        self.description_label.setSizePolicy(sizePolicy1)
        self.description_label.setMinimumSize(QSize(0, 75))
        self.description_label.setMaximumSize(QSize(480, 16777215))
        self.description_label.setTextFormat(Qt.RichText)
        self.description_label.setWordWrap(True)
        self.description_label.setOpenExternalLinks(True)

        self.gridLayout.addWidget(self.description_label, 2, 0, 1, 3)


        self.retranslateUi(CSGameExportDialog)

        QMetaObject.connectSlotsByName(CSGameExportDialog)
    # setupUi

    def retranslateUi(self, CSGameExportDialog):
        CSGameExportDialog.setWindowTitle(QCoreApplication.translate("CSGameExportDialog", u"Game Patching", None))
        self.output_file_button.setText(QCoreApplication.translate("CSGameExportDialog", u"Select File", None))
        self.auto_save_spoiler_check.setText(QCoreApplication.translate("CSGameExportDialog", u"Include a spoiler log on same directory", None))
        self.cancel_button.setText(QCoreApplication.translate("CSGameExportDialog", u"Cancel", None))
        self.output_file_label.setText(QCoreApplication.translate("CSGameExportDialog", u"Output Path", None))
        self.output_file_edit.setPlaceholderText(QCoreApplication.translate("CSGameExportDialog", u"Path where to place randomized game", None))
        self.accept_button.setText(QCoreApplication.translate("CSGameExportDialog", u"Accept", None))
        self.select_label.setText(QCoreApplication.translate("CSGameExportDialog", u"<html><head/><body><p>Select your preferred version of Cave Story:</p></body></html>", None))
        self.freeware_radio.setText(QCoreApplication.translate("CSGameExportDialog", u"Freeware", None))
        self.tweaked_radio.setText(QCoreApplication.translate("CSGameExportDialog", u"Tweaked", None))
        self.description_label.setText("")
    # retranslateUi

