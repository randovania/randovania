# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_customize_description.ui'
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
from PySide6.QtWidgets import (QApplication, QLabel, QMainWindow, QSizePolicy,
    QTextEdit, QVBoxLayout, QWidget)

class Ui_PresetCustomizeDescription(object):
    def setupUi(self, PresetCustomizeDescription):
        if not PresetCustomizeDescription.objectName():
            PresetCustomizeDescription.setObjectName(u"PresetCustomizeDescription")
        PresetCustomizeDescription.resize(476, 628)
        self.centralWidget = QWidget(PresetCustomizeDescription)
        self.centralWidget.setObjectName(u"centralWidget")
        self.centralWidget.setMaximumSize(QSize(16777215, 16777215))
        self.main_layout = QVBoxLayout(self.centralWidget)
        self.main_layout.setSpacing(6)
        self.main_layout.setContentsMargins(11, 11, 11, 11)
        self.main_layout.setObjectName(u"main_layout")
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(6, 6, 6, 6)
        self.description_label = QLabel(self.centralWidget)
        self.description_label.setObjectName(u"description_label")

        self.verticalLayout.addWidget(self.description_label)

        self.description_edit = QTextEdit(self.centralWidget)
        self.description_edit.setObjectName(u"description_edit")

        self.verticalLayout.addWidget(self.description_edit)


        self.main_layout.addLayout(self.verticalLayout)

        PresetCustomizeDescription.setCentralWidget(self.centralWidget)

        self.retranslateUi(PresetCustomizeDescription)

        QMetaObject.connectSlotsByName(PresetCustomizeDescription)
    # setupUi

    def retranslateUi(self, PresetCustomizeDescription):
        PresetCustomizeDescription.setWindowTitle(QCoreApplication.translate("PresetCustomizeDescription", u"Door Locks", None))
        self.description_label.setText(QCoreApplication.translate("PresetCustomizeDescription", u"Enter a description for your preset below.", None))
    # retranslateUi

