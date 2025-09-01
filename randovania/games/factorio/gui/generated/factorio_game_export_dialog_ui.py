# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'factorio_game_export_dialog.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QDialog, QFrame,
    QGridLayout, QLabel, QLineEdit, QPushButton,
    QSizePolicy, QWidget)

class Ui_FactorioGameExportDialog(object):
    def setupUi(self, FactorioGameExportDialog):
        if not FactorioGameExportDialog.objectName():
            FactorioGameExportDialog.setObjectName(u"FactorioGameExportDialog")
        FactorioGameExportDialog.resize(543, 351)
        self.root_layout = QGridLayout(FactorioGameExportDialog)
        self.root_layout.setSpacing(6)
        self.root_layout.setContentsMargins(11, 11, 11, 11)
        self.root_layout.setObjectName(u"root_layout")
        self.accept_button = QPushButton(FactorioGameExportDialog)
        self.accept_button.setObjectName(u"accept_button")

        self.root_layout.addWidget(self.accept_button, 16, 0, 1, 1)

        self.output_file_label = QLabel(FactorioGameExportDialog)
        self.output_file_label.setObjectName(u"output_file_label")

        self.root_layout.addWidget(self.output_file_label, 1, 0, 1, 1)

        self.output_file_button = QPushButton(FactorioGameExportDialog)
        self.output_file_button.setObjectName(u"output_file_button")

        self.root_layout.addWidget(self.output_file_button, 3, 1, 1, 1)

        self.download_assets_line = QFrame(FactorioGameExportDialog)
        self.download_assets_line.setObjectName(u"download_assets_line")
        self.download_assets_line.setFrameShape(QFrame.Shape.HLine)
        self.download_assets_line.setFrameShadow(QFrame.Shadow.Sunken)

        self.root_layout.addWidget(self.download_assets_line, 7, 0, 1, 2)

        self.use_default_button = QPushButton(FactorioGameExportDialog)
        self.use_default_button.setObjectName(u"use_default_button")

        self.root_layout.addWidget(self.use_default_button, 4, 1, 1, 1)

        self.output_file_edit = QLineEdit(FactorioGameExportDialog)
        self.output_file_edit.setObjectName(u"output_file_edit")

        self.root_layout.addWidget(self.output_file_edit, 3, 0, 1, 1)

        self.description_b_label = QLabel(FactorioGameExportDialog)
        self.description_b_label.setObjectName(u"description_b_label")
        self.description_b_label.setAlignment(Qt.AlignmentFlag.AlignJustify|Qt.AlignmentFlag.AlignVCenter)
        self.description_b_label.setWordWrap(True)
        self.description_b_label.setOpenExternalLinks(True)

        self.root_layout.addWidget(self.description_b_label, 5, 0, 1, 2)

        self.auto_save_spoiler_check = QCheckBox(FactorioGameExportDialog)
        self.auto_save_spoiler_check.setObjectName(u"auto_save_spoiler_check")

        self.root_layout.addWidget(self.auto_save_spoiler_check, 12, 0, 1, 1)

        self.download_assets_label = QLabel(FactorioGameExportDialog)
        self.download_assets_label.setObjectName(u"download_assets_label")
        self.download_assets_label.setTextFormat(Qt.TextFormat.MarkdownText)
        self.download_assets_label.setAlignment(Qt.AlignmentFlag.AlignJustify|Qt.AlignmentFlag.AlignVCenter)
        self.download_assets_label.setWordWrap(True)
        self.download_assets_label.setOpenExternalLinks(True)

        self.root_layout.addWidget(self.download_assets_label, 9, 0, 1, 2)

        self.line = QFrame(FactorioGameExportDialog)
        self.line.setObjectName(u"line")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.line.sizePolicy().hasHeightForWidth())
        self.line.setSizePolicy(sizePolicy)
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.root_layout.addWidget(self.line, 10, 0, 1, 2)

        self.cancel_button = QPushButton(FactorioGameExportDialog)
        self.cancel_button.setObjectName(u"cancel_button")

        self.root_layout.addWidget(self.cancel_button, 16, 1, 1, 1)

        self.description_a_label = QLabel(FactorioGameExportDialog)
        self.description_a_label.setObjectName(u"description_a_label")
        self.description_a_label.setTextFormat(Qt.TextFormat.MarkdownText)
        self.description_a_label.setOpenExternalLinks(True)

        self.root_layout.addWidget(self.description_a_label, 2, 0, 1, 1)

        self.description_c_label = QLabel(FactorioGameExportDialog)
        self.description_c_label.setObjectName(u"description_c_label")
        self.description_c_label.setTextFormat(Qt.TextFormat.MarkdownText)
        self.description_c_label.setOpenExternalLinks(True)

        self.root_layout.addWidget(self.description_c_label, 6, 0, 1, 2)


        self.retranslateUi(FactorioGameExportDialog)

        QMetaObject.connectSlotsByName(FactorioGameExportDialog)
    # setupUi

    def retranslateUi(self, FactorioGameExportDialog):
        FactorioGameExportDialog.setWindowTitle(QCoreApplication.translate("FactorioGameExportDialog", u"Factorio Mod Exporter", None))
        self.accept_button.setText(QCoreApplication.translate("FactorioGameExportDialog", u"Accept", None))
        self.output_file_label.setText(QCoreApplication.translate("FactorioGameExportDialog", u"Factorio Mods Folder", None))
        self.output_file_button.setText(QCoreApplication.translate("FactorioGameExportDialog", u"Select Folder", None))
        self.use_default_button.setText(QCoreApplication.translate("FactorioGameExportDialog", u"Use default", None))
        self.output_file_edit.setPlaceholderText(QCoreApplication.translate("FactorioGameExportDialog", u"Path of the Factorio mod folder", None))
        self.description_b_label.setText(QCoreApplication.translate("FactorioGameExportDialog", u"<html><head/><body><p>If playing from Steam, press &quot;Use default&quot;. On Linux, if using Flatpak Steam the default won't work.<br/>If you downloaded directly from Factorio.com, there will be a mods folder after opening the game once.</p></body></html>", None))
        self.auto_save_spoiler_check.setText(QCoreApplication.translate("FactorioGameExportDialog", u"Include a spoiler log on same directory", None))
        self.download_assets_label.setText(QCoreApplication.translate("FactorioGameExportDialog", u"During export, a [separate mod](https://mods.factorio.com/mod/randovania-assets) with all assets used by the randomizer is downloaded if it's not already present. ", None))
        self.cancel_button.setText(QCoreApplication.translate("FactorioGameExportDialog", u"Cancel", None))
        self.description_a_label.setText(QCoreApplication.translate("FactorioGameExportDialog", u"Select the [mods](https://wiki.factorio.com/Application_directory) folder for the Factorio install you are using.", None))
        self.description_c_label.setText(QCoreApplication.translate("FactorioGameExportDialog", u"For more details, see the [Application directory](https://wiki.factorio.com/Application_directory) and [Modding](https://wiki.factorio.com/Modding) pages of the Factorio Wiki.", None))
    # retranslateUi

