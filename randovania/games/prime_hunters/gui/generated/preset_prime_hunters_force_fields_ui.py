# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_prime_hunters_force_fields.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QGridLayout, QLabel,
    QMainWindow, QRadioButton, QScrollArea, QSizePolicy,
    QWidget)

class Ui_PresetHuntersForceFields(object):
    def setupUi(self, PresetHuntersForceFields):
        if not PresetHuntersForceFields.objectName():
            PresetHuntersForceFields.setObjectName(u"PresetHuntersForceFields")
        PresetHuntersForceFields.resize(466, 454)
        self.centralWidget = QWidget(PresetHuntersForceFields)
        self.centralWidget.setObjectName(u"centralWidget")
        self.centralWidget.setMaximumSize(QSize(16777215, 16777215))
        self.force_fields_top_layout = QGridLayout(self.centralWidget)
        self.force_fields_top_layout.setSpacing(6)
        self.force_fields_top_layout.setContentsMargins(11, 11, 11, 11)
        self.force_fields_top_layout.setObjectName(u"force_fields_top_layout")
        self.force_fields_top_layout.setContentsMargins(0, 4, 0, 0)
        self.scroll_area = QScrollArea(self.centralWidget)
        self.scroll_area.setObjectName(u"scroll_area")
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setFrameShadow(QFrame.Plain)
        self.scroll_area.setLineWidth(0)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.force_fields_scroll_contents = QWidget()
        self.force_fields_scroll_contents.setObjectName(u"force_fields_scroll_contents")
        self.force_fields_scroll_contents.setGeometry(QRect(0, 0, 466, 450))
        self.force_fields_layout = QGridLayout(self.force_fields_scroll_contents)
        self.force_fields_layout.setSpacing(6)
        self.force_fields_layout.setContentsMargins(11, 11, 11, 11)
        self.force_fields_layout.setObjectName(u"force_fields_layout")
        self.force_field_randomize_all_radiobutton = QRadioButton(self.force_fields_scroll_contents)
        self.force_field_randomize_all_radiobutton.setObjectName(u"force_field_randomize_all_radiobutton")

        self.force_fields_layout.addWidget(self.force_field_randomize_all_radiobutton, 2, 0, 1, 1)

        self.force_field_vanilla_radiobutton = QRadioButton(self.force_fields_scroll_contents)
        self.force_field_vanilla_radiobutton.setObjectName(u"force_field_vanilla_radiobutton")

        self.force_fields_layout.addWidget(self.force_field_vanilla_radiobutton, 1, 0, 1, 1)

        self.force_fields_description = QLabel(self.force_fields_scroll_contents)
        self.force_fields_description.setObjectName(u"force_fields_description")
        self.force_fields_description.setWordWrap(True)

        self.force_fields_layout.addWidget(self.force_fields_description, 0, 0, 1, 1)

        self.scroll_area.setWidget(self.force_fields_scroll_contents)

        self.force_fields_top_layout.addWidget(self.scroll_area, 0, 0, 1, 1)

        PresetHuntersForceFields.setCentralWidget(self.centralWidget)

        self.retranslateUi(PresetHuntersForceFields)

        QMetaObject.connectSlotsByName(PresetHuntersForceFields)
    # setupUi

    def retranslateUi(self, PresetHuntersForceFields):
        PresetHuntersForceFields.setWindowTitle(QCoreApplication.translate("PresetHuntersForceFields", u"Translators Gate", None))
        self.force_field_randomize_all_radiobutton.setText(QCoreApplication.translate("PresetHuntersForceFields", u"Randomize All", None))
        self.force_field_vanilla_radiobutton.setText(QCoreApplication.translate("PresetHuntersForceFields", u"Vanilla", None))
        self.force_fields_description.setText(QCoreApplication.translate("PresetHuntersForceFields", u"<html><head/><body><p>Change which weapons is required for all the force fields in the game. This includes force fields not used in the vanilla game, like Power Beam and Missiles. Their colors are changed to match the necessary weapon.</p></body></html>", None))
    # retranslateUi

