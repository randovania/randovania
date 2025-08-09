# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'area_details_popup.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialog, QDialogButtonBox,
    QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

from randovania.gui.lib.hint_feature_list_view import HintFeatureListView

class Ui_AreaDetailsPopup(object):
    def setupUi(self, AreaDetailsPopup):
        if not AreaDetailsPopup.objectName():
            AreaDetailsPopup.setObjectName(u"AreaDetailsPopup")
        AreaDetailsPopup.resize(350, 400)
        self.verticalLayout = QVBoxLayout(AreaDetailsPopup)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.name_layout = QHBoxLayout()
        self.name_layout.setObjectName(u"name_layout")
        self.name_label = QLabel(AreaDetailsPopup)
        self.name_label.setObjectName(u"name_label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.name_label.sizePolicy().hasHeightForWidth())
        self.name_label.setSizePolicy(sizePolicy)

        self.name_layout.addWidget(self.name_label)

        self.name_edit = QLineEdit(AreaDetailsPopup)
        self.name_edit.setObjectName(u"name_edit")

        self.name_layout.addWidget(self.name_edit)


        self.verticalLayout.addLayout(self.name_layout)

        self.hint_feature_box = HintFeatureListView(AreaDetailsPopup)
        self.hint_feature_box.setObjectName(u"hint_feature_box")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.hint_feature_box.sizePolicy().hasHeightForWidth())
        self.hint_feature_box.setSizePolicy(sizePolicy1)
        self.hint_feature_box.setMinimumSize(QSize(0, 0))

        self.verticalLayout.addWidget(self.hint_feature_box)

        self.extra_label = QLabel(AreaDetailsPopup)
        self.extra_label.setObjectName(u"extra_label")

        self.verticalLayout.addWidget(self.extra_label)

        self.extra_edit = QPlainTextEdit(AreaDetailsPopup)
        self.extra_edit.setObjectName(u"extra_edit")
        self.extra_edit.setMaximumSize(QSize(16777215, 100))

        self.verticalLayout.addWidget(self.extra_edit)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.button_box = QDialogButtonBox(AreaDetailsPopup)
        self.button_box.setObjectName(u"button_box")
        self.button_box.setOrientation(Qt.Orientation.Horizontal)
        self.button_box.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Save)

        self.verticalLayout.addWidget(self.button_box)


        self.retranslateUi(AreaDetailsPopup)

        QMetaObject.connectSlotsByName(AreaDetailsPopup)
    # setupUi

    def retranslateUi(self, AreaDetailsPopup):
        AreaDetailsPopup.setWindowTitle(QCoreApplication.translate("AreaDetailsPopup", u"Area Configuration", None))
        self.name_label.setText(QCoreApplication.translate("AreaDetailsPopup", u"Name:", None))
        self.hint_feature_box.setTitle(QCoreApplication.translate("AreaDetailsPopup", u"Hint Features", None))
        self.extra_label.setText(QCoreApplication.translate("AreaDetailsPopup", u"Extra:", None))
    # retranslateUi

