# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_echoes_hints.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QLabel, QMainWindow,
    QSizePolicy, QVBoxLayout, QWidget)

class Ui_PresetEchoesHints(object):
    def setupUi(self, PresetEchoesHints):
        if not PresetEchoesHints.objectName():
            PresetEchoesHints.setObjectName(u"PresetEchoesHints")
        PresetEchoesHints.resize(423, 259)
        self.centralWidget = QWidget(PresetEchoesHints)
        self.centralWidget.setObjectName(u"centralWidget")
        self.centralWidget.setMaximumSize(QSize(16777215, 16777215))
        self.hint_layout = QVBoxLayout(self.centralWidget)
        self.hint_layout.setSpacing(6)
        self.hint_layout.setContentsMargins(11, 11, 11, 11)
        self.hint_layout.setObjectName(u"hint_layout")
        self.hint_layout.setContentsMargins(4, 8, 4, 0)
        self.hint_sky_temple_key_label = QLabel(self.centralWidget)
        self.hint_sky_temple_key_label.setObjectName(u"hint_sky_temple_key_label")
        self.hint_sky_temple_key_label.setWordWrap(True)

        self.hint_layout.addWidget(self.hint_sky_temple_key_label)

        self.hint_sky_temple_key_combo = QComboBox(self.centralWidget)
        self.hint_sky_temple_key_combo.addItem("")
        self.hint_sky_temple_key_combo.addItem("")
        self.hint_sky_temple_key_combo.addItem("")
        self.hint_sky_temple_key_combo.setObjectName(u"hint_sky_temple_key_combo")

        self.hint_layout.addWidget(self.hint_sky_temple_key_combo)

        PresetEchoesHints.setCentralWidget(self.centralWidget)

        self.retranslateUi(PresetEchoesHints)

        QMetaObject.connectSlotsByName(PresetEchoesHints)
    # setupUi

    def retranslateUi(self, PresetEchoesHints):
        PresetEchoesHints.setWindowTitle(QCoreApplication.translate("PresetEchoesHints", u"Hints", None))
        self.hint_sky_temple_key_label.setText(QCoreApplication.translate("PresetEchoesHints", u"<html><head/><body><p>This controls how precise the hints for Sky Temple Keys in Sky Temple Gateway are.</p><p><span style=\" font-weight:600;\">No hints</span>: The scans provide no useful information.</p><p><span style=\" font-weight:600;\">Show only the area name</span>: Each scan says the corresponding key is in &quot;Temple Grounds&quot;, &quot;Agon Wastes&quot;, etc.<br/>Aether and Dark Aether are distinguished; for example, &quot;Agon Wastes&quot; refers only to the light world.</p><p><span style=\" font-weight:600;\">Show area and room name</span>: Each scan says the corresponding key is in &quot;Great Temple - Transport A Access&quot;, &quot;Ing Hive - Hive Entrance&quot;, etc. For rooms with more than one item location, there's no way to distinguish which one of them that key is in.</p></body></html>", None))
        self.hint_sky_temple_key_combo.setItemText(0, QCoreApplication.translate("PresetEchoesHints", u"No hints", None))
        self.hint_sky_temple_key_combo.setItemText(1, QCoreApplication.translate("PresetEchoesHints", u"Show only the area name", None))
        self.hint_sky_temple_key_combo.setItemText(2, QCoreApplication.translate("PresetEchoesHints", u"Show area and room name", None))

    # retranslateUi

