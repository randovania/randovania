# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'games_tab_supermetroid_widget.ui'
##
## Created by: Qt User Interface Compiler version 6.6.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import *  # type: ignore
from PySide6.QtGui import *  # type: ignore
from PySide6.QtWidgets import *  # type: ignore

from randovania.gui.widgets.generate_game_widget import *  # type: ignore

class Ui_SuperMetroidGameTabWidget(object):
    def setupUi(self, SuperMetroidGameTabWidget):
        if not SuperMetroidGameTabWidget.objectName():
            SuperMetroidGameTabWidget.setObjectName(u"SuperMetroidGameTabWidget")
        SuperMetroidGameTabWidget.resize(438, 393)
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

        SuperMetroidGameTabWidget.addTab(self.tab_intro, "")
        self.tab_generate_game = GenerateGameWidget()
        self.tab_generate_game.setObjectName(u"tab_generate_game")
        SuperMetroidGameTabWidget.addTab(self.tab_generate_game, "")
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
        self.faq_scroll_area_contents.setGeometry(QRect(0, 0, 432, 361))
        self.gridLayout_10 = QGridLayout(self.faq_scroll_area_contents)
        self.gridLayout_10.setSpacing(6)
        self.gridLayout_10.setContentsMargins(11, 11, 11, 11)
        self.gridLayout_10.setObjectName(u"gridLayout_10")
        self.faq_label = QLabel(self.faq_scroll_area_contents)
        self.faq_label.setObjectName(u"faq_label")
        self.faq_label.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.faq_label.setWordWrap(True)

        self.gridLayout_10.addWidget(self.faq_label, 0, 0, 1, 1)

        self.faq_scroll_area.setWidget(self.faq_scroll_area_contents)

        self.faq_layout.addWidget(self.faq_scroll_area, 0, 0, 1, 1)

        SuperMetroidGameTabWidget.addTab(self.faq_tab, "")

        self.retranslateUi(SuperMetroidGameTabWidget)

        SuperMetroidGameTabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(SuperMetroidGameTabWidget)
    # setupUi

    def retranslateUi(self, SuperMetroidGameTabWidget):
        self.game_cover_label.setText(QCoreApplication.translate("SuperMetroidGameTabWidget", u"TextLabel", None))
        self.intro_label.setText(QCoreApplication.translate("SuperMetroidGameTabWidget", u"<html><head/><body><p align=\"justify\">While answering the distress call of a Galactic Federation Space Station, Samus is attacked by Space Pirates and the last Metroid is stolen. Ridley, the Space Pirate leader, flees to Zebes with the Metroid. Explore the planet of Zebes, collect upgrades, defeat the 4 Space Pirate generals, and find the last Metroid!</p><p>The path to Mother Brain will not open until the victory conditions have been met. By default, this means defeating Kraid, Phantoon, Draygon, and Ridley.<br/><br/>Additional game patches have been applied to prevent common softlocks and create an overall smoother experience. Descriptions of these as well as the option to toggle them can be found in the preset options.<br/><br/>To get started, use the Quick Generate button below to generate a game using the default settings!</p></body></html>", None))
        self.quick_generate_button.setText(QCoreApplication.translate("SuperMetroidGameTabWidget", u"Quick generate", None))
        SuperMetroidGameTabWidget.setTabText(SuperMetroidGameTabWidget.indexOf(self.tab_intro), QCoreApplication.translate("SuperMetroidGameTabWidget", u"Introduction", None))
        SuperMetroidGameTabWidget.setTabText(SuperMetroidGameTabWidget.indexOf(self.tab_generate_game), QCoreApplication.translate("SuperMetroidGameTabWidget", u"Play", None))
        self.faq_label.setText(QCoreApplication.translate("SuperMetroidGameTabWidget", u"# updated from code", None))
        SuperMetroidGameTabWidget.setTabText(SuperMetroidGameTabWidget.indexOf(self.faq_tab), QCoreApplication.translate("SuperMetroidGameTabWidget", u"FAQ", None))
        pass
    # retranslateUi

