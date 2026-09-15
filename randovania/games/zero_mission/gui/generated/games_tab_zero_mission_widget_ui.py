# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'games_tab_zero_mission_widget.ui'
##
## Created by: tools/uic_wrapper.py
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

class Ui_MZMGameTabWidget(object):
    def setupUi(self, MZMGameTabWidget):
        if not MZMGameTabWidget.objectName():
            MZMGameTabWidget.setObjectName(u"MZMGameTabWidget")
        MZMGameTabWidget.resize(501, 393)
        MZMGameTabWidget.setDocumentMode(True)
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

        MZMGameTabWidget.addTab(self.tab_intro, "")
        self.tab_generate_game = GenerateGameWidget()
        self.tab_generate_game.setObjectName(u"tab_generate_game")
        MZMGameTabWidget.addTab(self.tab_generate_game, "")
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
        self.faq_scroll_area_contents.setGeometry(QRect(0, 0, 497, 365))
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

        MZMGameTabWidget.addTab(self.faq_tab, "")
        self.differences_tab = QWidget()
        self.differences_tab.setObjectName(u"differences_tab")
        self.horizontalLayout = QHBoxLayout(self.differences_tab)
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setContentsMargins(11, 11, 11, 11)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.differences_scroll_area = QScrollArea(self.differences_tab)
        self.differences_scroll_area.setObjectName(u"differences_scroll_area")
        self.differences_scroll_area.setWidgetResizable(True)
        self.differences_scroll_contents = QWidget()
        self.differences_scroll_contents.setObjectName(u"differences_scroll_contents")
        self.differences_scroll_contents.setGeometry(QRect(0, 0, 467, 637))
        self.verticalLayout = QVBoxLayout(self.differences_scroll_contents)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.differences_label = QLabel(self.differences_scroll_contents)
        self.differences_label.setObjectName(u"differences_label")
        self.differences_label.setTextFormat(Qt.TextFormat.MarkdownText)
        self.differences_label.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        self.differences_label.setWordWrap(True)

        self.verticalLayout.addWidget(self.differences_label)

        self.differences_scroll_area.setWidget(self.differences_scroll_contents)

        self.horizontalLayout.addWidget(self.differences_scroll_area)

        MZMGameTabWidget.addTab(self.differences_tab, "")
        self.pickup_hint_features_tab = PickupHintFeatureTab()
        self.pickup_hint_features_tab.setObjectName(u"pickup_hint_features_tab")
        MZMGameTabWidget.addTab(self.pickup_hint_features_tab, "")

        self.retranslateUi(MZMGameTabWidget)

        MZMGameTabWidget.setCurrentIndex(3)


        QMetaObject.connectSlotsByName(MZMGameTabWidget)
    # setupUi

    def retranslateUi(self, MZMGameTabWidget):
        self.game_cover_label.setText(QCoreApplication.translate("MZMGameTabWidget", u"TextLabel", None))
        self.intro_label.setText(QCoreApplication.translate("MZMGameTabWidget", u"<html><head/><body><p align=\"justify\">The Blank game is used by Randovania to serve as an example of how a game is integrated.</p></body></html>", None))
        self.quick_generate_button.setText(QCoreApplication.translate("MZMGameTabWidget", u"Quick generate", None))
        MZMGameTabWidget.setTabText(MZMGameTabWidget.indexOf(self.tab_intro), QCoreApplication.translate("MZMGameTabWidget", u"Introduction", None))
        MZMGameTabWidget.setTabText(MZMGameTabWidget.indexOf(self.tab_generate_game), QCoreApplication.translate("MZMGameTabWidget", u"Play", None))
        self.faq_label.setText(QCoreApplication.translate("MZMGameTabWidget", u"# updated from code", None))
        MZMGameTabWidget.setTabText(MZMGameTabWidget.indexOf(self.faq_tab), QCoreApplication.translate("MZMGameTabWidget", u"FAQ", None))
        self.differences_label.setText(QCoreApplication.translate("MZMGameTabWidget", u"Randovania and the MARS patcher make some changes to the original game in order to improve the randomizer experience or to simply fix bugs in the original game. Key differences are: \n"
"\n"
"### Gameplay\n"
"\n"
"- New Launcher items have been added for Missiles, Super Missiles, and Power Bombs which are required to use their respective ammo.\n"
"\n"
"- New movement items have been added for Springball, Infinite Bomb Jump, and Wall Jump Boots.\n"
"\n"
"- The Ruins Test event is no longer required to activate Space Jump, Gravity Suit, or Plasma Beam. The Ruins Test is now a pickup location.\n"
"\n"
"- The Zipline activation is now shuffled into the pool as a pickup. The Zipline activation platform is now a pickup location.\n"
"\n"
"- Deorem will only spawn when the player has collected Missile Launcher and no longer flees. Deorem only spawns in the first location near the Norfair elevator.\n"
"\n"
"- The Acid Worm and Ridley now always spawn regardless of the events.\n"
"\n"
"- The suitless sequence has been r"
                        "emoved.\n"
"\n"
"- Missile Hatches are no longer weak to Super Missiles.\n"
"\n"
"- Hatches locked by events now revert to their correct types.\n"
"\n"
"- TODO: Say something about goal here...\n"
"\n"
"### Room Changes\n"
"\n"
"- Crateria - TODO - The Chozo pillar is now always extended.\n"
"\n"
"- Norfair - TODO - The Imago Cocoon room now always has tunnels.\n"
"\n"
"### Quality of Life\n"
"\n"
"- You can now warp to start by pressing L on the map screen. All progress since your last save will be lost. This is NEVER considered logical.\n"
"\n"
"- On the inventory screen, you can now enable/disable acquired powerups.\n"
"\n"
"- Ammo drop rates have been reworked so that Super Missiles will drop when Missiles are not acquired and Power Bombs will always drop when Health and Missile ammo is full.\n"
"\n"
"- A cosmetic setting has been added to reveal all hidden blocks.\n"
"\n"
"\n"
"", None))
        MZMGameTabWidget.setTabText(MZMGameTabWidget.indexOf(self.differences_tab), QCoreApplication.translate("MZMGameTabWidget", u"Differences", None))
        MZMGameTabWidget.setTabText(MZMGameTabWidget.indexOf(self.pickup_hint_features_tab), QCoreApplication.translate("MZMGameTabWidget", u"Pickup Hint Features", None))
        pass
    # retranslateUi

