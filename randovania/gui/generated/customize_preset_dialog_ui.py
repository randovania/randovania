# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'customize_preset_dialog.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QAbstractItemView, QApplication, QDialog,
    QDialogButtonBox, QFrame, QHBoxLayout, QLabel,
    QLineEdit, QListView, QListWidget, QListWidgetItem,
    QSizePolicy, QStackedWidget, QVBoxLayout, QWidget)

class Ui_CustomizePresetDialog(object):
    def setupUi(self, CustomizePresetDialog):
        if not CustomizePresetDialog.objectName():
            CustomizePresetDialog.setObjectName(u"CustomizePresetDialog")
        CustomizePresetDialog.resize(952, 717)
        self.root_layout = QVBoxLayout(CustomizePresetDialog)
        self.root_layout.setSpacing(0)
        self.root_layout.setContentsMargins(11, 11, 11, 11)
        self.root_layout.setObjectName(u"root_layout")
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.name_layout = QHBoxLayout()
        self.name_layout.setSpacing(0)
        self.name_layout.setObjectName(u"name_layout")
        self.name_layout.setContentsMargins(6, 6, 6, 6)
        self.name_label = QLabel(CustomizePresetDialog)
        self.name_label.setObjectName(u"name_label")

        self.name_layout.addWidget(self.name_label)

        self.name_edit = QLineEdit(CustomizePresetDialog)
        self.name_edit.setObjectName(u"name_edit")

        self.name_layout.addWidget(self.name_edit)


        self.root_layout.addLayout(self.name_layout)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.line = QFrame(CustomizePresetDialog)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.line)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.listWidget = QListWidget(CustomizePresetDialog)
        self.listWidget.setObjectName(u"listWidget")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.listWidget.sizePolicy().hasHeightForWidth())
        self.listWidget.setSizePolicy(sizePolicy)
        self.listWidget.setBaseSize(QSize(0, 0))
        self.listWidget.setFrameShape(QFrame.NoFrame)
        self.listWidget.setFrameShadow(QFrame.Plain)
        self.listWidget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.listWidget.setEditTriggers(QAbstractItemView.SelectedClicked)
        self.listWidget.setFlow(QListView.TopToBottom)
        self.listWidget.setResizeMode(QListView.Adjust)
        self.listWidget.setSpacing(0)

        self.horizontalLayout.addWidget(self.listWidget)

        self.line_3 = QFrame(CustomizePresetDialog)
        self.line_3.setObjectName(u"line_3")
        self.line_3.setFrameShape(QFrame.Shape.VLine)
        self.line_3.setFrameShadow(QFrame.Shadow.Sunken)

        self.horizontalLayout.addWidget(self.line_3)

        self.stackedWidget = QStackedWidget(CustomizePresetDialog)
        self.stackedWidget.setObjectName(u"stackedWidget")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.stackedWidget.sizePolicy().hasHeightForWidth())
        self.stackedWidget.setSizePolicy(sizePolicy1)
        self.stackedWidget.setFrameShape(QFrame.NoFrame)

        self.horizontalLayout.addWidget(self.stackedWidget)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.line_2 = QFrame(CustomizePresetDialog)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.Shape.HLine)
        self.line_2.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.line_2)


        self.root_layout.addLayout(self.verticalLayout)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setSpacing(6)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(6, 6, 6, 6)
        self.button_box = QDialogButtonBox(CustomizePresetDialog)
        self.button_box.setObjectName(u"button_box")
        self.button_box.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Save)

        self.verticalLayout_2.addWidget(self.button_box)


        self.root_layout.addLayout(self.verticalLayout_2)


        self.retranslateUi(CustomizePresetDialog)

        QMetaObject.connectSlotsByName(CustomizePresetDialog)
    # setupUi

    def retranslateUi(self, CustomizePresetDialog):
        CustomizePresetDialog.setWindowTitle(QCoreApplication.translate("CustomizePresetDialog", u"Customize Preset", None))
        self.name_label.setText(QCoreApplication.translate("CustomizePresetDialog", u"Name:", None))
    # retranslateUi

