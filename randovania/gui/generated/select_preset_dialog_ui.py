# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'select_preset_dialog.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QDialog, QGridLayout,
    QLabel, QLineEdit, QPushButton, QSizePolicy,
    QWidget)

from randovania.gui.widgets.select_preset_widget import SelectPresetWidget

class Ui_SelectPresetDialog(object):
    def setupUi(self, SelectPresetDialog):
        if not SelectPresetDialog.objectName():
            SelectPresetDialog.setObjectName(u"SelectPresetDialog")
        SelectPresetDialog.resize(548, 438)
        self.gridLayout = QGridLayout(SelectPresetDialog)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setContentsMargins(11, 11, 11, 11)
        self.gridLayout.setObjectName(u"gridLayout")
        self.world_name_edit = QLineEdit(SelectPresetDialog)
        self.world_name_edit.setObjectName(u"world_name_edit")

        self.gridLayout.addWidget(self.world_name_edit, 0, 1, 1, 1)

        self.world_name_label = QLabel(SelectPresetDialog)
        self.world_name_label.setObjectName(u"world_name_label")

        self.gridLayout.addWidget(self.world_name_label, 0, 0, 1, 1)

        self.game_selection_combo = QComboBox(SelectPresetDialog)
        self.game_selection_combo.setObjectName(u"game_selection_combo")

        self.gridLayout.addWidget(self.game_selection_combo, 1, 0, 1, 2)

        self.accept_button = QPushButton(SelectPresetDialog)
        self.accept_button.setObjectName(u"accept_button")

        self.gridLayout.addWidget(self.accept_button, 3, 0, 1, 1)

        self.select_preset_widget = SelectPresetWidget(SelectPresetDialog)
        self.select_preset_widget.setObjectName(u"select_preset_widget")

        self.gridLayout.addWidget(self.select_preset_widget, 2, 0, 1, 2)

        self.cancel_button = QPushButton(SelectPresetDialog)
        self.cancel_button.setObjectName(u"cancel_button")

        self.gridLayout.addWidget(self.cancel_button, 3, 1, 1, 1)


        self.retranslateUi(SelectPresetDialog)

        QMetaObject.connectSlotsByName(SelectPresetDialog)
    # setupUi

    def retranslateUi(self, SelectPresetDialog):
        SelectPresetDialog.setWindowTitle(QCoreApplication.translate("SelectPresetDialog", u"Select Preset", None))
        self.world_name_edit.setPlaceholderText(QCoreApplication.translate("SelectPresetDialog", u"World name", None))
        self.world_name_label.setText(QCoreApplication.translate("SelectPresetDialog", u"World name", None))
        self.accept_button.setText(QCoreApplication.translate("SelectPresetDialog", u"Accept", None))
        self.cancel_button.setText(QCoreApplication.translate("SelectPresetDialog", u"Cancel", None))
    # retranslateUi

