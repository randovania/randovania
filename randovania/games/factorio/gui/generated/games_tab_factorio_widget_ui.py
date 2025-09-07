# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'games_tab_factorio_widget.ui'
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

class Ui_FactorioGameTabWidget(object):
    def setupUi(self, FactorioGameTabWidget):
        if not FactorioGameTabWidget.objectName():
            FactorioGameTabWidget.setObjectName(u"FactorioGameTabWidget")
        FactorioGameTabWidget.resize(501, 393)
        FactorioGameTabWidget.setDocumentMode(True)
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
        self.intro_label.setTextFormat(Qt.TextFormat.MarkdownText)
        self.intro_label.setWordWrap(True)

        self.intro_cover_layout.addWidget(self.intro_label)


        self.intro_layout.addLayout(self.intro_cover_layout)

        self.quick_generate_button = QPushButton(self.tab_intro)
        self.quick_generate_button.setObjectName(u"quick_generate_button")

        self.intro_layout.addWidget(self.quick_generate_button)

        self.intro_spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.intro_layout.addItem(self.intro_spacer)

        FactorioGameTabWidget.addTab(self.tab_intro, "")
        self.tab_generate_game = GenerateGameWidget()
        self.tab_generate_game.setObjectName(u"tab_generate_game")
        FactorioGameTabWidget.addTab(self.tab_generate_game, "")
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

        FactorioGameTabWidget.addTab(self.faq_tab, "")
        self.differences_tab = QWidget()
        self.differences_tab.setObjectName(u"differences_tab")
        self.differences_layout = QVBoxLayout(self.differences_tab)
        self.differences_layout.setSpacing(6)
        self.differences_layout.setContentsMargins(11, 11, 11, 11)
        self.differences_layout.setObjectName(u"differences_layout")
        self.differences_layout.setContentsMargins(0, 0, 0, 0)
        self.differences_scroll_area = QScrollArea(self.differences_tab)
        self.differences_scroll_area.setObjectName(u"differences_scroll_area")
        self.differences_scroll_area.setWidgetResizable(True)
        self.differences_scroll_area_contents = QWidget()
        self.differences_scroll_area_contents.setObjectName(u"differences_scroll_area_contents")
        self.differences_scroll_area_contents.setGeometry(QRect(0, 0, 485, 929))
        self.differences_scroll_layout = QVBoxLayout(self.differences_scroll_area_contents)
        self.differences_scroll_layout.setSpacing(6)
        self.differences_scroll_layout.setContentsMargins(11, 11, 11, 11)
        self.differences_scroll_layout.setObjectName(u"differences_scroll_layout")
        self.differences_label = QLabel(self.differences_scroll_area_contents)
        self.differences_label.setObjectName(u"differences_label")
        self.differences_label.setTextFormat(Qt.TextFormat.MarkdownText)
        self.differences_label.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        self.differences_label.setWordWrap(True)

        self.differences_scroll_layout.addWidget(self.differences_label)

        self.differences_scroll_area.setWidget(self.differences_scroll_area_contents)

        self.differences_layout.addWidget(self.differences_scroll_area)

        FactorioGameTabWidget.addTab(self.differences_tab, "")
        self.pickup_hint_features_tab = PickupHintFeatureTab()
        self.pickup_hint_features_tab.setObjectName(u"pickup_hint_features_tab")
        FactorioGameTabWidget.addTab(self.pickup_hint_features_tab, "")

        self.retranslateUi(FactorioGameTabWidget)

        FactorioGameTabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(FactorioGameTabWidget)
    # setupUi

    def retranslateUi(self, FactorioGameTabWidget):
        self.game_cover_label.setText(QCoreApplication.translate("FactorioGameTabWidget", u"TextLabel", None))
        self.intro_label.setText(QCoreApplication.translate("FactorioGameTabWidget", u"Build a factory, research new technologies and automate the whole process in order to launch a rocket.\n"
"\n"
"What each technology you unlock gives is shuffled, but which science packs you'll need and how many is still the same. However, the recipes for each pack plus the rocket and satellite are random!", None))
        self.quick_generate_button.setText(QCoreApplication.translate("FactorioGameTabWidget", u"Quick generate", None))
        FactorioGameTabWidget.setTabText(FactorioGameTabWidget.indexOf(self.tab_intro), QCoreApplication.translate("FactorioGameTabWidget", u"Introduction", None))
        FactorioGameTabWidget.setTabText(FactorioGameTabWidget.indexOf(self.tab_generate_game), QCoreApplication.translate("FactorioGameTabWidget", u"Play", None))
        self.faq_label.setText(QCoreApplication.translate("FactorioGameTabWidget", u"# updated from code", None))
        FactorioGameTabWidget.setTabText(FactorioGameTabWidget.indexOf(self.faq_tab), QCoreApplication.translate("FactorioGameTabWidget", u"FAQ", None))
        self.differences_label.setText(QCoreApplication.translate("FactorioGameTabWidget", u"### Freebies\n"
"Whenever a technology is researched, any eligible items from the unlocked recipes are distributed to online players as bonus.\n"
"\n"
"Using buildings acquired by freebies is expected by logic, such as solar panels for power.\n"
"\n"
"#### Eligible Items\n"
"- Placeable entities, such as buildings and robots.\n"
"- Armors, equipment and guns.\n"
"\n"
"### New Items and Recipes\n"
"- Burner Assembling Machine and Burner Lab have been added, always available.\n"
"- Longer Handed Inserters have been added, with a unique technology to unlock them.\n"
"- Alternative recipes for handcrafting Construction and Logistic Robots were added.\n"
"\n"
"### Starting Items and Recipes\n"
"- Transport Belts are now unlocked by Logistics 1, along with Underground Belts and Splitters.\n"
"- Pipes and Pipe to Ground are now unlocked by default, instead of by Steam Power.\n"
"- Copper Cable, Small Electric Poles, Iron Stick and Labs are once again unlocked by default.\n"
"\n"
"### Inserter Changes\n"
"- Inserters "
                        "now have their own technology, progressive with Fast Inserters and Bulk Inserters.\n"
"- Long Handed Inserters are unlocked by their own technology, separately from other Inserters.\n"
"- Inserter Capactity Bonus is split into Regular and Bulk Inserter Capacity Bonus.\n"
"\n"
"### Fluid Changes\n"
"- Fluid Handling now only unlocks barreling recipes.\n"
"- New technology Fluid Storage has been added that unlocks Fluid Tanks and Pumps.\n"
"- Fluid Wagons no longer have Storage Tanks as an ingredient and the technology also unlocks Pumps.\n"
"\n"
"### Oil Changes\n"
"- Solid Fuel recipes are now unlocked only by the new technology Solid Fuel.\n"
"- Heavy and Light Oil Cracking are now unlocked by the Oil Cracking technology.\n"
"- Coal Liquefaction now uses Steam as an ingredient instead of Heavy Oil and also unlocks Refineries.\n"
"\n"
"### Changed and New Technologies\n"
"- Electronics now unlocks only Electronic Circuits.\n"
"- Medium Electric Pole and Big Electric Pole are now unlocked by separate technologi"
                        "es.\n"
"- Research Productivity has been added.\n"
"- Research Speed and Mining Productivity now give high bonuses per level.\n"
"- Automated rail transportation has been merged with Railway.\n"
"- Nuclear Fuel Reprocessing has been merged with Nuclear Power.", None))
        FactorioGameTabWidget.setTabText(FactorioGameTabWidget.indexOf(self.differences_tab), QCoreApplication.translate("FactorioGameTabWidget", u"Differences", None))
        FactorioGameTabWidget.setTabText(FactorioGameTabWidget.indexOf(self.pickup_hint_features_tab), QCoreApplication.translate("FactorioGameTabWidget", u"Pickup Hint Features", None))
        pass
    # retranslateUi

