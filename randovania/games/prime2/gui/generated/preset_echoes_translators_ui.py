# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_echoes_translators.ui'
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
    QMainWindow, QPushButton, QScrollArea, QSizePolicy,
    QWidget)

class Ui_PresetEchoesTranslators(object):
    def setupUi(self, PresetEchoesTranslators):
        if not PresetEchoesTranslators.objectName():
            PresetEchoesTranslators.setObjectName(u"PresetEchoesTranslators")
        PresetEchoesTranslators.resize(466, 454)
        self.centralWidget = QWidget(PresetEchoesTranslators)
        self.centralWidget.setObjectName(u"centralWidget")
        self.centralWidget.setMaximumSize(QSize(16777215, 16777215))
        self.translators_top_layout = QGridLayout(self.centralWidget)
        self.translators_top_layout.setSpacing(6)
        self.translators_top_layout.setContentsMargins(11, 11, 11, 11)
        self.translators_top_layout.setObjectName(u"translators_top_layout")
        self.translators_top_layout.setContentsMargins(0, 4, 0, 0)
        self.scroll_area = QScrollArea(self.centralWidget)
        self.scroll_area.setObjectName(u"scroll_area")
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setFrameShadow(QFrame.Plain)
        self.scroll_area.setLineWidth(0)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.translators_scroll_contents = QWidget()
        self.translators_scroll_contents.setObjectName(u"translators_scroll_contents")
        self.translators_scroll_contents.setGeometry(QRect(0, 0, 466, 450))
        self.translators_layout = QGridLayout(self.translators_scroll_contents)
        self.translators_layout.setSpacing(6)
        self.translators_layout.setContentsMargins(11, 11, 11, 11)
        self.translators_layout.setObjectName(u"translators_layout")
        self.translators_layout.setContentsMargins(0, 0, 0, 0)
        self.translator_vanilla_colors_button = QPushButton(self.translators_scroll_contents)
        self.translator_vanilla_colors_button.setObjectName(u"translator_vanilla_colors_button")

        self.translators_layout.addWidget(self.translator_vanilla_colors_button, 2, 0, 1, 1)

        self.translator_vanilla_actual_button = QPushButton(self.translators_scroll_contents)
        self.translator_vanilla_actual_button.setObjectName(u"translator_vanilla_actual_button")

        self.translators_layout.addWidget(self.translator_vanilla_actual_button, 1, 0, 1, 1)

        self.translator_randomize_all_button = QPushButton(self.translators_scroll_contents)
        self.translator_randomize_all_button.setObjectName(u"translator_randomize_all_button")

        self.translators_layout.addWidget(self.translator_randomize_all_button, 1, 2, 1, 1)

        self.translator_randomize_all_with_unlocked_button = QPushButton(self.translators_scroll_contents)
        self.translator_randomize_all_with_unlocked_button.setObjectName(u"translator_randomize_all_with_unlocked_button")

        self.translators_layout.addWidget(self.translator_randomize_all_with_unlocked_button, 2, 2, 1, 1)

        self.translators_description = QLabel(self.translators_scroll_contents)
        self.translators_description.setObjectName(u"translators_description")
        self.translators_description.setWordWrap(True)

        self.translators_layout.addWidget(self.translators_description, 0, 0, 1, 3)

        self.scroll_area.setWidget(self.translators_scroll_contents)

        self.translators_top_layout.addWidget(self.scroll_area, 0, 0, 1, 1)

        PresetEchoesTranslators.setCentralWidget(self.centralWidget)

        self.retranslateUi(PresetEchoesTranslators)

        QMetaObject.connectSlotsByName(PresetEchoesTranslators)
    # setupUi

    def retranslateUi(self, PresetEchoesTranslators):
        PresetEchoesTranslators.setWindowTitle(QCoreApplication.translate("PresetEchoesTranslators", u"Translators Gate", None))
        self.translator_vanilla_colors_button.setText(QCoreApplication.translate("PresetEchoesTranslators", u"Vanilla (Colors)", None))
        self.translator_vanilla_actual_button.setText(QCoreApplication.translate("PresetEchoesTranslators", u"Vanilla (Actual)", None))
        self.translator_randomize_all_button.setText(QCoreApplication.translate("PresetEchoesTranslators", u"Randomize All", None))
        self.translator_randomize_all_with_unlocked_button.setText(QCoreApplication.translate("PresetEchoesTranslators", u"Randomize All with Unlocked", None))
        self.translators_description.setText(QCoreApplication.translate("PresetEchoesTranslators", u"<html><head/><body><p>Change which translator is required for all the gates in the game. Their colors are changed to match the necessary translator.</p><p>There are two vanilla options: using the actual translator requirements in the game, and using the vanilla gate colors.<br/>This is because in the original game, some translator gates are colored one way, but the translator requirement is something else.</p><p>The Emerald gate in Great Temple - Temple Sanctuary has a special case, when elevators aren't vanilla: if you enter Great Temple via Transport A, it will be permanently down.</p></body></html>", None))
    # retranslateUi

