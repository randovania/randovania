# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'games_tab_prime_hunters_widget.ui'
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
from PySide6.QtWidgets import (QApplication, QGridLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QSizePolicy, QSpacerItem,
    QTabWidget, QVBoxLayout, QWidget)

from randovania.gui.widgets.generate_game_widget import GenerateGameWidget
from randovania.gui.widgets.hint_feature_tab import PickupHintFeatureTab

class Ui_HuntersGameTabWidget(object):
    def setupUi(self, HuntersGameTabWidget):
        if not HuntersGameTabWidget.objectName():
            HuntersGameTabWidget.setObjectName(u"HuntersGameTabWidget")
        HuntersGameTabWidget.resize(501, 393)
        HuntersGameTabWidget.setDocumentMode(True)
        self.tab_intro = QWidget()
        self.tab_intro.setObjectName(u"tab_intro")
        self.intro_layout = QVBoxLayout(self.tab_intro)
        self.intro_layout.setSpacing(6)
        self.intro_layout.setContentsMargins(11, 11, 11, 11)
        self.intro_layout.setObjectName(u"intro_layout")
        self.intro_cover_layout = QHBoxLayout()
        self.intro_cover_layout.setSpacing(6)
        self.intro_cover_layout.setObjectName(u"intro_cover_layout")
        self.game_cover_label = QLabel(self.tab_intro)
        self.game_cover_label.setObjectName(u"game_cover_label")

        self.intro_cover_layout.addWidget(self.game_cover_label)

        self.intro_label = QLabel(self.tab_intro)
        self.intro_label.setObjectName(u"intro_label")
        self.intro_label.setWordWrap(True)

        self.intro_cover_layout.addWidget(self.intro_label)


        self.intro_layout.addLayout(self.intro_cover_layout)

        self.quick_generate_button = QPushButton(self.tab_intro)
        self.quick_generate_button.setObjectName(u"quick_generate_button")

        self.intro_layout.addWidget(self.quick_generate_button)

        self.intro_spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.intro_layout.addItem(self.intro_spacer)

        HuntersGameTabWidget.addTab(self.tab_intro, "")
        self.tab_generate_game = GenerateGameWidget()
        self.tab_generate_game.setObjectName(u"tab_generate_game")
        HuntersGameTabWidget.addTab(self.tab_generate_game, "")
        self.faq_tab = QWidget()
        self.faq_tab.setObjectName(u"faq_tab")
        self.faq_layout = QGridLayout(self.faq_tab)
        self.faq_layout.setSpacing(6)
        self.faq_layout.setContentsMargins(11, 11, 11, 11)
        self.faq_layout.setObjectName(u"faq_layout")
        self.faq_layout.setContentsMargins(0, 0, 0, 0)
        self.faq_scroll_area = QScrollArea(self.faq_tab)
        self.faq_scroll_area.setObjectName(u"faq_scroll_area")
        self.faq_scroll_area.setWidgetResizable(True)
        self.faq_scroll_area_contents = QWidget()
        self.faq_scroll_area_contents.setObjectName(u"faq_scroll_area_contents")
        self.faq_scroll_area_contents.setGeometry(QRect(0, 0, 499, 363))
        self.faq_scroll_layout = QGridLayout(self.faq_scroll_area_contents)
        self.faq_scroll_layout.setSpacing(6)
        self.faq_scroll_layout.setContentsMargins(11, 11, 11, 11)
        self.faq_scroll_layout.setObjectName(u"faq_scroll_layout")
        self.faq_label = QLabel(self.faq_scroll_area_contents)
        self.faq_label.setObjectName(u"faq_label")
        self.faq_label.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        self.faq_label.setWordWrap(True)

        self.faq_scroll_layout.addWidget(self.faq_label, 0, 0, 1, 1)

        self.faq_scroll_area.setWidget(self.faq_scroll_area_contents)

        self.faq_layout.addWidget(self.faq_scroll_area, 0, 0, 1, 1)

        HuntersGameTabWidget.addTab(self.faq_tab, "")
        self.pickup_hint_features_tab = PickupHintFeatureTab()
        self.pickup_hint_features_tab.setObjectName(u"pickup_hint_features_tab")
        HuntersGameTabWidget.addTab(self.pickup_hint_features_tab, "")

        self.retranslateUi(HuntersGameTabWidget)

        HuntersGameTabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(HuntersGameTabWidget)
    # setupUi

    def retranslateUi(self, HuntersGameTabWidget):
        self.game_cover_label.setText(QCoreApplication.translate("HuntersGameTabWidget", u"TextLabel", None))
        self.intro_label.setText(QCoreApplication.translate("HuntersGameTabWidget", u"<html><head/><body><p align=\"justify\">Explore the ruins of the Alimbic Cluster and recover the Octoliths, then activate the Alimbic Cannon to open the Oubliette and defeat Gorea.</p><p>To get started, use the Quick Generate button to generate a game using the default settings!</p></body></html>", None))
        self.quick_generate_button.setText(QCoreApplication.translate("HuntersGameTabWidget", u"Quick generate", None))
        HuntersGameTabWidget.setTabText(HuntersGameTabWidget.indexOf(self.tab_intro), QCoreApplication.translate("HuntersGameTabWidget", u"Introduction", None))
        HuntersGameTabWidget.setTabText(HuntersGameTabWidget.indexOf(self.tab_generate_game), QCoreApplication.translate("HuntersGameTabWidget", u"Play", None))
        self.faq_label.setText(QCoreApplication.translate("HuntersGameTabWidget", u"# updated from code", None))
        HuntersGameTabWidget.setTabText(HuntersGameTabWidget.indexOf(self.faq_tab), QCoreApplication.translate("HuntersGameTabWidget", u"FAQ", None))
        HuntersGameTabWidget.setTabText(HuntersGameTabWidget.indexOf(self.pickup_hint_features_tab), QCoreApplication.translate("HuntersGameTabWidget", u"Pickup Hint Features", None))
        pass
    # retranslateUi

