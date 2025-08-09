# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_dread_lights.ui'
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
from PySide6.QtWidgets import (QApplication, QGroupBox, QHBoxLayout, QLabel,
    QMainWindow, QPushButton, QScrollArea, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)

class Ui_PresetDreadLights(object):
    def setupUi(self, PresetDreadLights):
        if not PresetDreadLights.objectName():
            PresetDreadLights.setObjectName(u"PresetDreadLights")
        PresetDreadLights.resize(438, 284)
        self.central_widget = QWidget(PresetDreadLights)
        self.central_widget.setObjectName(u"central_widget")
        self.central_widget.setMaximumSize(QSize(16777215, 16777215))
        self.central_layout = QVBoxLayout(self.central_widget)
        self.central_layout.setSpacing(6)
        self.central_layout.setContentsMargins(11, 11, 11, 11)
        self.central_layout.setObjectName(u"central_layout")
        self.central_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_area = QScrollArea(self.central_widget)
        self.scroll_area.setObjectName(u"scroll_area")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_contents = QWidget()
        self.scroll_contents.setObjectName(u"scroll_contents")
        self.scroll_contents.setGeometry(QRect(0, 0, 436, 282))
        self.scroll_layout = QVBoxLayout(self.scroll_contents)
        self.scroll_layout.setSpacing(6)
        self.scroll_layout.setContentsMargins(11, 11, 11, 11)
        self.scroll_layout.setObjectName(u"scroll_layout")
        self.scroll_layout.setContentsMargins(0, 2, 0, 0)
        self.top_spacer = QSpacerItem(20, 8, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.scroll_layout.addItem(self.top_spacer)

        self.lights_out_box = QGroupBox(self.scroll_contents)
        self.lights_out_box.setObjectName(u"lights_out_box")
        self.lights_out_layout = QVBoxLayout(self.lights_out_box)
        self.lights_out_layout.setSpacing(6)
        self.lights_out_layout.setContentsMargins(11, 11, 11, 11)
        self.lights_out_layout.setObjectName(u"lights_out_layout")
        self.lights_out_label = QLabel(self.lights_out_box)
        self.lights_out_label.setObjectName(u"lights_out_label")

        self.lights_out_layout.addWidget(self.lights_out_label)

        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.setSpacing(6)
        self.buttons_layout.setObjectName(u"buttons_layout")
        self.enable_button = QPushButton(self.lights_out_box)
        self.enable_button.setObjectName(u"enable_button")

        self.buttons_layout.addWidget(self.enable_button)

        self.disable_button = QPushButton(self.lights_out_box)
        self.disable_button.setObjectName(u"disable_button")

        self.buttons_layout.addWidget(self.disable_button)


        self.lights_out_layout.addLayout(self.buttons_layout)


        self.scroll_layout.addWidget(self.lights_out_box)

        self.bottom_spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.scroll_layout.addItem(self.bottom_spacer)

        self.scroll_area.setWidget(self.scroll_contents)

        self.central_layout.addWidget(self.scroll_area)

        PresetDreadLights.setCentralWidget(self.central_widget)

        self.retranslateUi(PresetDreadLights)

        QMetaObject.connectSlotsByName(PresetDreadLights)
    # setupUi

    def retranslateUi(self, PresetDreadLights):
        PresetDreadLights.setWindowTitle(QCoreApplication.translate("PresetDreadLights", u"Lights", None))
        self.lights_out_box.setTitle(QCoreApplication.translate("PresetDreadLights", u"Lights out", None))
        self.lights_out_label.setText(QCoreApplication.translate("PresetDreadLights", u"If a region is enabled, every light source within it will be removed.\n"
"This setting makes the game very dark, but still somewhat visible.", None))
        self.enable_button.setText(QCoreApplication.translate("PresetDreadLights", u"Enable All", None))
        self.disable_button.setText(QCoreApplication.translate("PresetDreadLights", u"Disable All", None))
    # retranslateUi

