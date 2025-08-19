# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'games_tab_cavestory_widget.ui'
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
from PySide6.QtWidgets import (QApplication, QGridLayout, QHBoxLayout, QHeaderView,
    QLabel, QPushButton, QScrollArea, QSizePolicy,
    QSpacerItem, QTabWidget, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout, QWidget)

from randovania.gui.widgets.generate_game_widget import GenerateGameWidget
from randovania.gui.widgets.hint_feature_tab import (LocationHintFeatureTab, PickupHintFeatureTab)

class Ui_CaveStoryGameTabWidget(object):
    def setupUi(self, CaveStoryGameTabWidget):
        if not CaveStoryGameTabWidget.objectName():
            CaveStoryGameTabWidget.setObjectName(u"CaveStoryGameTabWidget")
        CaveStoryGameTabWidget.resize(423, 416)
        CaveStoryGameTabWidget.setDocumentMode(True)
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
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.intro_label.sizePolicy().hasHeightForWidth())
        self.intro_label.setSizePolicy(sizePolicy)
        self.intro_label.setWordWrap(True)

        self.intro_cover_layout.addWidget(self.intro_label)


        self.intro_layout.addLayout(self.intro_cover_layout)

        self.quick_generate_button = QPushButton(self.tab_intro)
        self.quick_generate_button.setObjectName(u"quick_generate_button")

        self.intro_layout.addWidget(self.quick_generate_button)

        self.intro_spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.intro_layout.addItem(self.intro_spacer)

        CaveStoryGameTabWidget.addTab(self.tab_intro, "")
        self.tab_generate_game = GenerateGameWidget()
        self.tab_generate_game.setObjectName(u"tab_generate_game")
        CaveStoryGameTabWidget.addTab(self.tab_generate_game, "")
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
        self.faq_scroll_area_contents.setGeometry(QRect(0, 0, 421, 386))
        self.gridLayout_9 = QGridLayout(self.faq_scroll_area_contents)
        self.gridLayout_9.setSpacing(6)
        self.gridLayout_9.setContentsMargins(11, 11, 11, 11)
        self.gridLayout_9.setObjectName(u"gridLayout_9")
        self.custom_faq_label = QLabel(self.faq_scroll_area_contents)
        self.custom_faq_label.setObjectName(u"custom_faq_label")
        self.custom_faq_label.setTextFormat(Qt.MarkdownText)
        self.custom_faq_label.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.custom_faq_label.setWordWrap(True)

        self.gridLayout_9.addWidget(self.custom_faq_label, 0, 0, 1, 1)

        self.faq_scroll_area.setWidget(self.faq_scroll_area_contents)

        self.faq_layout.addWidget(self.faq_scroll_area, 0, 0, 1, 1)

        CaveStoryGameTabWidget.addTab(self.faq_tab, "")
        self.differences_tab = QWidget()
        self.differences_tab.setObjectName(u"differences_tab")
        self.differences_tab_layout = QVBoxLayout(self.differences_tab)
        self.differences_tab_layout.setSpacing(6)
        self.differences_tab_layout.setContentsMargins(11, 11, 11, 11)
        self.differences_tab_layout.setObjectName(u"differences_tab_layout")
        self.differences_tab_layout.setContentsMargins(0, 0, 0, 0)
        self.differences_scroll_area = QScrollArea(self.differences_tab)
        self.differences_scroll_area.setObjectName(u"differences_scroll_area")
        self.differences_scroll_area.setWidgetResizable(True)
        self.differences_scroll_contents = QWidget()
        self.differences_scroll_contents.setObjectName(u"differences_scroll_contents")
        self.differences_scroll_contents.setGeometry(QRect(0, 0, 407, 1040))
        self.differences_scroll_layout_4 = QVBoxLayout(self.differences_scroll_contents)
        self.differences_scroll_layout_4.setSpacing(6)
        self.differences_scroll_layout_4.setContentsMargins(11, 11, 11, 11)
        self.differences_scroll_layout_4.setObjectName(u"differences_scroll_layout_4")
        self.differences_label = QLabel(self.differences_scroll_contents)
        self.differences_label.setObjectName(u"differences_label")
        self.differences_label.setTextFormat(Qt.MarkdownText)
        self.differences_label.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.differences_label.setWordWrap(True)

        self.differences_scroll_layout_4.addWidget(self.differences_label)

        self.differences_scroll_area.setWidget(self.differences_scroll_contents)

        self.differences_tab_layout.addWidget(self.differences_scroll_area)

        CaveStoryGameTabWidget.addTab(self.differences_tab, "")
        self.hints_tab = QWidget()
        self.hints_tab.setObjectName(u"hints_tab")
        self.hints_tab_layout = QVBoxLayout(self.hints_tab)
        self.hints_tab_layout.setSpacing(0)
        self.hints_tab_layout.setContentsMargins(11, 11, 11, 11)
        self.hints_tab_layout.setObjectName(u"hints_tab_layout")
        self.hints_tab_layout.setContentsMargins(0, 0, 0, 0)
        self.hints_scroll_area = QScrollArea(self.hints_tab)
        self.hints_scroll_area.setObjectName(u"hints_scroll_area")
        self.hints_scroll_area.setWidgetResizable(True)
        self.hints_scroll_area_contents = QWidget()
        self.hints_scroll_area_contents.setObjectName(u"hints_scroll_area_contents")
        self.hints_scroll_area_contents.setGeometry(QRect(0, 0, 421, 386))
        self.hints_scroll_layout = QVBoxLayout(self.hints_scroll_area_contents)
        self.hints_scroll_layout.setSpacing(6)
        self.hints_scroll_layout.setContentsMargins(11, 11, 11, 11)
        self.hints_scroll_layout.setObjectName(u"hints_scroll_layout")
        self.hints_label = QLabel(self.hints_scroll_area_contents)
        self.hints_label.setObjectName(u"hints_label")
        self.hints_label.setTextFormat(Qt.MarkdownText)
        self.hints_label.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.hints_label.setWordWrap(True)

        self.hints_scroll_layout.addWidget(self.hints_label)

        self.hints_scroll_area.setWidget(self.hints_scroll_area_contents)

        self.hints_tab_layout.addWidget(self.hints_scroll_area)

        CaveStoryGameTabWidget.addTab(self.hints_tab, "")
        self.pickup_hint_features_tab = PickupHintFeatureTab()
        self.pickup_hint_features_tab.setObjectName(u"pickup_hint_features_tab")
        self.hint_item_names_layout = QVBoxLayout(self.pickup_hint_features_tab)
        self.hint_item_names_layout.setSpacing(0)
        self.hint_item_names_layout.setContentsMargins(11, 11, 11, 11)
        self.hint_item_names_layout.setObjectName(u"hint_item_names_layout")
        self.hint_item_names_layout.setContentsMargins(0, 0, 0, 0)
        CaveStoryGameTabWidget.addTab(self.pickup_hint_features_tab, "")
        self.location_hint_features_tab = LocationHintFeatureTab()
        self.location_hint_features_tab.setObjectName(u"location_hint_features_tab")
        CaveStoryGameTabWidget.addTab(self.location_hint_features_tab, "")
        self.hint_locations_tab = QWidget()
        self.hint_locations_tab.setObjectName(u"hint_locations_tab")
        self.hint_tab_layout = QVBoxLayout(self.hint_locations_tab)
        self.hint_tab_layout.setSpacing(6)
        self.hint_tab_layout.setContentsMargins(11, 11, 11, 11)
        self.hint_tab_layout.setObjectName(u"hint_tab_layout")
        self.hint_tab_layout.setContentsMargins(0, 0, 0, 0)
        self.hint_locations_scroll_area = QScrollArea(self.hint_locations_tab)
        self.hint_locations_scroll_area.setObjectName(u"hint_locations_scroll_area")
        self.hint_locations_scroll_area.setWidgetResizable(True)
        self.hint_locations_scroll_area.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.hint_locations_scroll_contents = QWidget()
        self.hint_locations_scroll_contents.setObjectName(u"hint_locations_scroll_contents")
        self.hint_locations_scroll_contents.setGeometry(QRect(0, 0, 421, 386))
        self.hint_scroll_layout = QVBoxLayout(self.hint_locations_scroll_contents)
        self.hint_scroll_layout.setSpacing(6)
        self.hint_scroll_layout.setContentsMargins(11, 11, 11, 11)
        self.hint_scroll_layout.setObjectName(u"hint_scroll_layout")
        self.hint_locations_label = QLabel(self.hint_locations_scroll_contents)
        self.hint_locations_label.setObjectName(u"hint_locations_label")
        self.hint_locations_label.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.hint_locations_label.setWordWrap(True)

        self.hint_scroll_layout.addWidget(self.hint_locations_label)

        self.hint_locations_tree_widget = QTreeWidget(self.hint_locations_scroll_contents)
        self.hint_locations_tree_widget.setObjectName(u"hint_locations_tree_widget")

        self.hint_scroll_layout.addWidget(self.hint_locations_tree_widget)

        self.hint_locations_scroll_area.setWidget(self.hint_locations_scroll_contents)

        self.hint_tab_layout.addWidget(self.hint_locations_scroll_area)

        CaveStoryGameTabWidget.addTab(self.hint_locations_tab, "")

        self.retranslateUi(CaveStoryGameTabWidget)

        CaveStoryGameTabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(CaveStoryGameTabWidget)
    # setupUi

    def retranslateUi(self, CaveStoryGameTabWidget):
        self.game_cover_label.setText(QCoreApplication.translate("CaveStoryGameTabWidget", u"[game cover]", None))
        self.intro_label.setText(QCoreApplication.translate("CaveStoryGameTabWidget", u"<html><head/><body><p align=\"justify\">Navigate the floating island, finding items in all sorts of places, then make your way to one of the game's three endings! </p><p align=\"justify\">The default preset starts with the Map System and Nikumaru Counter. Check the Map System from your inventory at any time to see how many items you have collected. Along the way, speak to Cthulhus and blue robots to receive hints on where items are hidden. </p><p align=\"justify\">The objective is to achieve the Normal Ending - to do this, you need to save Sue in the Egg Corridor and build the rocket in Plantation. </p><p align=\"justify\">For more details, check the FAQ and Differences tabs. To get started, use the Quick Generate button to generate a game using the default settings.</p><p align=\"justify\">&quot;Then play and have a fun!&quot;</p></body></html>", None))
        self.quick_generate_button.setText(QCoreApplication.translate("CaveStoryGameTabWidget", u"Quick generate", None))
        CaveStoryGameTabWidget.setTabText(CaveStoryGameTabWidget.indexOf(self.tab_intro), QCoreApplication.translate("CaveStoryGameTabWidget", u"Introduction", None))
        CaveStoryGameTabWidget.setTabText(CaveStoryGameTabWidget.indexOf(self.tab_generate_game), QCoreApplication.translate("CaveStoryGameTabWidget", u"Play", None))
        self.custom_faq_label.setText(QCoreApplication.translate("CaveStoryGameTabWidget", u"## Help me!\n"
"If you find yourself stuck, here are a few common pitfalls:\n"
"- Remember that the Jellyfish Juice can quench more than one fireplace\n"
"- The Graveyard can only be accessed if you obtain the Silver Locket and see Toroko get kidnapped\n"
"- The Hermit Gunsmith will wake up and give you an item if you defeat the Core and show him his gun\n"
"- The western side of the Labyrinth can be accessed without flight if you defeat Toroko+\n"
"- The Plantation can be accessed without the Teleporter Room Key if you save Kazuma and teleport in or climb the Outer Wall\n"
"- The Waterway can be accessed without the Cure-All by using the teleporter in the Labyrinth Shop\n"
"- There may be a required item in the Last Cave (Hidden) as a reward for defeating the Red Demon\n"
"\n"
"If you're still stuck, join our [official Discord server](https://discord.gg/7zUdPEn) and ask for help in there!", None))
        CaveStoryGameTabWidget.setTabText(CaveStoryGameTabWidget.indexOf(self.faq_tab), QCoreApplication.translate("CaveStoryGameTabWidget", u"FAQ", None))
        self.differences_label.setText(QCoreApplication.translate("CaveStoryGameTabWidget", u"## Main differences\n"
"Note that there are a few key differences from the vanilla game in order to improve the playing experience:\n"
"\n"
"- All 5 teleporter locations in Arthur's House are active from the beginning of the game\n"
"- All other teleporters from the vanilla game are active and linked to one another at all times\n"
"- A teleporter between Sand Zone (near the Storehouse) and Labyrinth I has been placed and can be activated in one of two ways:\n"
"   1. Defeating Toroko+\n"
"   2. Using the teleporter from the Labyrinth I side\n"
"- Most cutscenes have been abridged or skipped entirely\n"
"- Jellyfish Juice can be used an infinite number of times\n"
"- You can carry as many as 5 puppies at once: Jenka will only accept them once you've collected all 5\n"
"- Certain items that are received from NPCs have been placed in chests:\n"
"  - Labyrinth B (Fallen Booster)\n"
"  - Labyrinth Shop\n"
"    - One requiring the Machine Gun to open\n"
"    - One requiring the Fireball to open\n"
"    - One requiri"
                        "ng the Spur to open\n"
"  - Jail no. 1\n"
"  - Storage? (Ma Pignon)\n"
"    - This chest requires saving Curly in the Waterway to open\n"
"- If you don't have Curly's Air Tank after defeating the Core, the water will not rise and you may leave without dying\n"
"- Curly cannot be left behind permanently in the Core; the shutter will never close once the boss has been defeated\n"
"- The jump in the Waterway to save Curly has been made much easier\n"
"- Ironhead will always give you his item on defeat (but there's still a special surprise if you defeat him without taking damage!)\n"
"- Kazuma will only open the door between Egg no. 0 and the Outer Wall if you save him in Grasstown\n"
"- Kazuma's door can be blown down from both the outside and the inside\n"
"- Entering the Throne Room to complete the game requires doing a few things:\n"
"  1. Saving Sue in the Egg Corridor\n"
"  2. Obtaining the Booster 2.0 (for Best Ending and up)\n"
"  3. Obtaining the Iron Bond (for Best Ending and up)\n"
"  4. Defeating every"
                        " boss (for All Bosses and up)\n"
"  5. Obtaining all 66 items outside of Sacred Grounds (for 100%)\n"
"- In Bad Ending, leaving the island with Kazuma on the Outer Wall requires two things:\n"
"  1. Saving Kazuma using the Explosive\n"
"  2. Defeating the Core", None))
        CaveStoryGameTabWidget.setTabText(CaveStoryGameTabWidget.indexOf(self.differences_tab), QCoreApplication.translate("CaveStoryGameTabWidget", u"Differences", None))
        self.hints_label.setText(QCoreApplication.translate("CaveStoryGameTabWidget", u"In Cave Story, you can find hints from the following sources:\n"
"\n"
"**Blue Robots and Cthulhus**: Each of these friendly folks will provide a general hint about items in the game.\n"
"\n"
"**MALCO**: MALCO provides a hint about the item he gives as a reward for bringing him the bomb ingredients.\n"
"\n"
"**Jenka**: Jenka provides a hint about the item she gives as a reward for returning all 5 of her puppies.\n"
"\n"
"**Mrs. Little**: Mrs. Little provides a hint about the item Mr. Little gives as a reward for returning him home and showing him the Blade.\n"
"\n"
"**Numahachi**: In the Statue Chamber, Numahachi will provide two hints about the items found in Sacred Grounds.", None))
        CaveStoryGameTabWidget.setTabText(CaveStoryGameTabWidget.indexOf(self.hints_tab), QCoreApplication.translate("CaveStoryGameTabWidget", u"Hints", None))
        CaveStoryGameTabWidget.setTabText(CaveStoryGameTabWidget.indexOf(self.pickup_hint_features_tab), QCoreApplication.translate("CaveStoryGameTabWidget", u"Pickup Hint Features", None))
        CaveStoryGameTabWidget.setTabText(CaveStoryGameTabWidget.indexOf(self.location_hint_features_tab), QCoreApplication.translate("CaveStoryGameTabWidget", u"Location Hint Features", None))
        self.hint_locations_label.setText(QCoreApplication.translate("CaveStoryGameTabWidget", u"<html><head/><body><p>Hints\n"
"                                                are placed in the game by replacing character dialog.\n"
"                                                The following are the areas that may have a hint added\n"
"                                                to them:</p></body></html>\n"
"                                            ", None))
        ___qtreewidgetitem = self.hint_locations_tree_widget.headerItem()
        ___qtreewidgetitem.setText(0, QCoreApplication.translate("CaveStoryGameTabWidget", u"Location", None));
        CaveStoryGameTabWidget.setTabText(CaveStoryGameTabWidget.indexOf(self.hint_locations_tab), QCoreApplication.translate("CaveStoryGameTabWidget", u"Hint Locations", None))
        pass
    # retranslateUi

