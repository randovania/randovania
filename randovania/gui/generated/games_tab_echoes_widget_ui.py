# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'games_tab_echoes_widget.ui'
##
## Created by: Qt User Interface Compiler version 6.6.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import *  # type: ignore
from PySide6.QtGui import *  # type: ignore
from PySide6.QtWidgets import *  # type: ignore

from randovania.gui.widgets.generate_game_widget import *  # type: ignore

class Ui_EchoesGameTabWidget(object):
    def setupUi(self, EchoesGameTabWidget):
        if not EchoesGameTabWidget.objectName():
            EchoesGameTabWidget.setObjectName(u"EchoesGameTabWidget")
        EchoesGameTabWidget.resize(446, 396)
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

        EchoesGameTabWidget.addTab(self.tab_intro, "")
        self.tab_generate_game = GenerateGameWidget()
        self.tab_generate_game.setObjectName(u"tab_generate_game")
        EchoesGameTabWidget.addTab(self.tab_generate_game, "")
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
        self.faq_scroll_area_contents.setGeometry(QRect(0, 0, 440, 370))
        self.gridLayout_8 = QGridLayout(self.faq_scroll_area_contents)
        self.gridLayout_8.setSpacing(6)
        self.gridLayout_8.setContentsMargins(11, 11, 11, 11)
        self.gridLayout_8.setObjectName(u"gridLayout_8")
        self.faq_label = QLabel(self.faq_scroll_area_contents)
        self.faq_label.setObjectName(u"faq_label")
        self.faq_label.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.faq_label.setWordWrap(True)

        self.gridLayout_8.addWidget(self.faq_label, 0, 0, 1, 1)

        self.faq_scroll_area.setWidget(self.faq_scroll_area_contents)

        self.faq_layout.addWidget(self.faq_scroll_area, 0, 0, 1, 1)

        EchoesGameTabWidget.addTab(self.faq_tab, "")
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
        self.differences_scroll_contents.setGeometry(QRect(0, 0, 430, 732))
        self.differences_scroll_layout_3 = QVBoxLayout(self.differences_scroll_contents)
        self.differences_scroll_layout_3.setSpacing(6)
        self.differences_scroll_layout_3.setContentsMargins(11, 11, 11, 11)
        self.differences_scroll_layout_3.setObjectName(u"differences_scroll_layout_3")
        self.differences_label = QLabel(self.differences_scroll_contents)
        self.differences_label.setObjectName(u"differences_label")
        self.differences_label.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.differences_label.setWordWrap(True)

        self.differences_scroll_layout_3.addWidget(self.differences_label)

        self.differences_scroll_area.setWidget(self.differences_scroll_contents)

        self.differences_tab_layout.addWidget(self.differences_scroll_area)

        EchoesGameTabWidget.addTab(self.differences_tab, "")
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
        self.hints_scroll_area_contents.setGeometry(QRect(0, 0, 430, 672))
        self.hints_scroll_layout = QVBoxLayout(self.hints_scroll_area_contents)
        self.hints_scroll_layout.setSpacing(6)
        self.hints_scroll_layout.setContentsMargins(11, 11, 11, 11)
        self.hints_scroll_layout.setObjectName(u"hints_scroll_layout")
        self.hints_label = QLabel(self.hints_scroll_area_contents)
        self.hints_label.setObjectName(u"hints_label")
        self.hints_label.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.hints_label.setWordWrap(True)

        self.hints_scroll_layout.addWidget(self.hints_label)

        self.hints_scroll_area.setWidget(self.hints_scroll_area_contents)

        self.hints_tab_layout.addWidget(self.hints_scroll_area)

        EchoesGameTabWidget.addTab(self.hints_tab, "")
        self.hint_item_names_tab = QWidget()
        self.hint_item_names_tab.setObjectName(u"hint_item_names_tab")
        self.hint_item_names_layout = QVBoxLayout(self.hint_item_names_tab)
        self.hint_item_names_layout.setSpacing(0)
        self.hint_item_names_layout.setContentsMargins(11, 11, 11, 11)
        self.hint_item_names_layout.setObjectName(u"hint_item_names_layout")
        self.hint_item_names_layout.setContentsMargins(0, 0, 0, 0)
        self.hint_item_names_scroll_area = QScrollArea(self.hint_item_names_tab)
        self.hint_item_names_scroll_area.setObjectName(u"hint_item_names_scroll_area")
        self.hint_item_names_scroll_area.setWidgetResizable(True)
        self.hint_item_names_scroll_area.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.hint_item_names_scroll_contents = QWidget()
        self.hint_item_names_scroll_contents.setObjectName(u"hint_item_names_scroll_contents")
        self.hint_item_names_scroll_contents.setGeometry(QRect(0, 0, 440, 370))
        self.hint_item_names_scroll_layout = QVBoxLayout(self.hint_item_names_scroll_contents)
        self.hint_item_names_scroll_layout.setSpacing(6)
        self.hint_item_names_scroll_layout.setContentsMargins(11, 11, 11, 11)
        self.hint_item_names_scroll_layout.setObjectName(u"hint_item_names_scroll_layout")
        self.hint_item_names_label = QLabel(self.hint_item_names_scroll_contents)
        self.hint_item_names_label.setObjectName(u"hint_item_names_label")
        self.hint_item_names_label.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.hint_item_names_label.setWordWrap(True)

        self.hint_item_names_scroll_layout.addWidget(self.hint_item_names_label)

        self.hint_item_names_tree_widget = QTableWidget(self.hint_item_names_scroll_contents)
        if (self.hint_item_names_tree_widget.columnCount() < 4):
            self.hint_item_names_tree_widget.setColumnCount(4)
        __qtablewidgetitem = QTableWidgetItem()
        self.hint_item_names_tree_widget.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.hint_item_names_tree_widget.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.hint_item_names_tree_widget.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.hint_item_names_tree_widget.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        self.hint_item_names_tree_widget.setObjectName(u"hint_item_names_tree_widget")
        self.hint_item_names_tree_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.hint_item_names_tree_widget.setSortingEnabled(True)

        self.hint_item_names_scroll_layout.addWidget(self.hint_item_names_tree_widget)

        self.hint_item_names_scroll_area.setWidget(self.hint_item_names_scroll_contents)

        self.hint_item_names_layout.addWidget(self.hint_item_names_scroll_area)

        EchoesGameTabWidget.addTab(self.hint_item_names_tab, "")
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
        self.hint_locations_scroll_contents.setGeometry(QRect(0, 0, 440, 370))
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

        EchoesGameTabWidget.addTab(self.hint_locations_tab, "")

        self.retranslateUi(EchoesGameTabWidget)

        EchoesGameTabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(EchoesGameTabWidget)
    # setupUi

    def retranslateUi(self, EchoesGameTabWidget):
        self.game_cover_label.setText(QCoreApplication.translate("EchoesGameTabWidget", u"TextLabel", None))
        self.intro_label.setText(QCoreApplication.translate("EchoesGameTabWidget", u"<html><head/><body><p align=\"justify\">Navigate Aether and Dark Aether in search of the Sky Temple Keys, then defeat Emperor Ing and Dark Samus to finish!</p><p align=\"justify\">The totems in Sky Temple Gateway can be scanned to receive hints on the locations of each Sky Temple Key. Additionally, Keybearer corpses can be scanned to receive hints for the corresponding Flying Ing Cache, and Luminoth Lore can be scanned to receive generic hints for any items or locations. </p><p align=\"justify\">To get started, use the Quick Generate button to generate a game using the default settings!</p></body></html>", None))
        self.quick_generate_button.setText(QCoreApplication.translate("EchoesGameTabWidget", u"Quick generate", None))
        EchoesGameTabWidget.setTabText(EchoesGameTabWidget.indexOf(self.tab_intro), QCoreApplication.translate("EchoesGameTabWidget", u"Introduction", None))
        EchoesGameTabWidget.setTabText(EchoesGameTabWidget.indexOf(self.tab_generate_game), QCoreApplication.translate("EchoesGameTabWidget", u"Play", None))
        self.faq_label.setText(QCoreApplication.translate("EchoesGameTabWidget", u"# updated from code", None))
        EchoesGameTabWidget.setTabText(EchoesGameTabWidget.indexOf(self.faq_tab), QCoreApplication.translate("EchoesGameTabWidget", u"FAQ", None))
        self.differences_label.setText(QCoreApplication.translate("EchoesGameTabWidget", u"<html><head/><body><p>Randovania\n"
"                                                makes some changes to the original game in order to\n"
"                                                improve the game experience or to simply fix bugs in the\n"
"                                                original game.</p><p>Many of these changes\n"
"                                                are optional and can be disabled in the many options\n"
"                                                Randovania provides, but the following are <span\n"
"                                                style=\" font-weight:600;\">always</span>\n"
"                                                there:</p><ul style=\"margin-top: 0px;\n"
"                                                margin-bottom: 0px; margin-left: 0px; margin-right: 0px;\n"
"                                                -qt-list-indent: 1;\"><li style=\"\n"
"                                                margin-top:12px; margin-bottom:12px; margin-l"
                        "eft:0px;\n"
"                                                margin-right:0px; -qt-block-indent:0; text-indent:0px;\">The\n"
"                                                item loss cutscene in Hive Chamber B is disabled.</li><li\n"
"                                                style=\" margin-top:12px; margin-bottom:12px;\n"
"                                                margin-left:0px; margin-right:0px; -qt-block-indent:0;\n"
"                                                text-indent:0px;\">Instead of acquiring the\n"
"                                                translators by scanning the hologram, there is now an\n"
"                                                item pickup in the Energy Controllers. This item is thus\n"
"                                                randomized.</li><li style=\"\n"
"                                                margin-top:12px; margin-bottom:12px; margin-left:0px;\n"
"                                                margin-right:0px; -qt-block-indent:0; "
                        "text-indent:0px;\">All\n"
"                                                cutscenes are skippable by default.</li><li\n"
"                                                style=\" margin-top:12px; margin-bottom:12px;\n"
"                                                margin-left:0px; margin-right:0px; -qt-block-indent:0;\n"
"                                                text-indent:0px;\">Hard Mode and the Image\n"
"                                                gallery are unlocked by default.</li><li style=\"\n"
"                                                margin-top:12px; margin-bottom:12px; margin-left:0px;\n"
"                                                margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Starting\n"
"                                                the Dark Samus 1 fight disables adjacent rooms from\n"
"                                                loading automatically (fixes a potential crash).</li><li\n"
"                                                style=\" margin"
                        "-top:12px; margin-bottom:12px;\n"
"                                                margin-left:0px; margin-right:0px; -qt-block-indent:0;\n"
"                                                text-indent:0px;\">Beating Dark Samus 1 will now\n"
"                                                turn off the first pass pirates layer in Biostorage\n"
"                                                Station (fixes a potential crash).</li><li\n"
"                                                style=\" margin-top:12px; margin-bottom:12px;\n"
"                                                margin-left:0px; margin-right:0px; -qt-block-indent:0;\n"
"                                                text-indent:0px;\">Agon Temple's first door no\n"
"                                                longer stays locked after Bomb Guardian until you get\n"
"                                                the Agon Energy Controller item.</li><li style=\"\n"
"                                                margin-top:12px; margin"
                        "-bottom:12px; margin-left:0px;\n"
"                                                margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Leaving\n"
"                                                during the Grapple Guardian fight no longer causes\n"
"                                                Grapple Guardian to not drop an item if you come back\n"
"                                                and fight it again.</li><li style=\"\n"
"                                                margin-top:12px; margin-bottom:12px; margin-left:0px;\n"
"                                                margin-right:0px; -qt-block-indent:0; text-indent:0px;\">The\n"
"                                                Luminoth barriers that appear on certain doors after\n"
"                                                collecting or returning a world's energy have been\n"
"                                                removed.</li><li style=\" margin-top:12px;\n"
"                                                margi"
                        "n-bottom:12px; margin-left:0px; margin-right:0px;\n"
"                                                -qt-block-indent:0; text-indent:0px;\">Removed\n"
"                                                some instances in Main Research, to decrease the chance\n"
"                                                of a crash coming from Central Area Transport West. Also\n"
"                                                fixed leaving the room midway through destroying the\n"
"                                                echo locks making it impossible to complete.</li><li\n"
"                                                style=\" margin-top:12px; margin-bottom:12px;\n"
"                                                margin-left:0px; margin-right:0px; -qt-block-indent:0;\n"
"                                                text-indent:0px;\">Power Bombs no longer\n"
"                                                instantly kill either Alpha Splinter's first phase or\n"
"                                         "
                        "       Spider Guardian (doing so would not actually end the\n"
"                                                fight, leaving you stuck).</li><li style=\"\n"
"                                                margin-top:12px; margin-bottom:12px; margin-left:0px;\n"
"                                                margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Getting\n"
"                                                the Torvus Energy Controller item will no longer block\n"
"                                                you from getting the Torvus Temple item.</li><li\n"
"                                                style=\" margin-top:12px; margin-bottom:12px;\n"
"                                                margin-left:0px; margin-right:0px; -qt-block-indent:0;\n"
"                                                text-indent:0px;\">Fixed the door lock in\n"
"                                                Bioenergy Production, so that it doesn't stay locked if\n"
"                           "
                        "                     you beat the Aerotroopers before triggering the lock.</li><li\n"
"                                                style=\" margin-top:12px; margin-bottom:12px;\n"
"                                                margin-left:0px; margin-right:0px; -qt-block-indent:0;\n"
"                                                text-indent:0px;\">Altered a few rooms (Transport\n"
"                                                A Access, Venomous Pond) so that the PAL version matches\n"
"                                                NTSC requirements.</li><li style=\"\n"
"                                                margin-top:12px; margin-bottom:12px; margin-left:0px;\n"
"                                                margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Fixed\n"
"                                                the message when collecting the item in Mining Station B\n"
"                                                while in the wrong layer.</li><li style=\"\n"
"         "
                        "                                       margin-top:12px; margin-bottom:12px; margin-left:0px;\n"
"                                                margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Added\n"
"                                                a warning when going on top of the ship in GFMC Compound\n"
"                                                before beating Jump Guardian.</li><li style=\"\n"
"                                                margin-top:12px; margin-bottom:12px; margin-left:0px;\n"
"                                                margin-right:0px; -qt-block-indent:0; text-indent:0px;\">The\n"
"                                                in-game Hint System has been removed. The option for it\n"
"                                                remains, but does nothing.</li><li style=\"\n"
"                                                margin-top:12px; margin-bottom:12px; margin-left:0px;\n"
"                                                margin-right:0px; -qt-block-"
                        "indent:0; text-indent:0px;\">The\n"
"                                                logbook entries that contains hints are now named after\n"
"                                                the room they're in, with the categories being about\n"
"                                                which kind of hint they are.</li><li style=\"\n"
"                                                margin-top:12px; margin-bottom:12px; margin-left:0px;\n"
"                                                margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Agon,\n"
"                                                Torvus and Sanctuary Energy Controllers are alwyas\n"
"                                                visible in the map, to allow warping with the light\n"
"                                                beams.</li><li style=\" margin-top:12px;\n"
"                                                margin-bottom:12px; margin-left:0px; margin-right:0px;\n"
"                                                -"
                        "qt-block-indent:0; text-indent:0px;\">When a\n"
"                                                crash happens, the game now displays an error screen\n"
"                                                instead of just stopping.</li></ul></body></html>\n"
"                                            ", None))
        EchoesGameTabWidget.setTabText(EchoesGameTabWidget.indexOf(self.differences_tab), QCoreApplication.translate("EchoesGameTabWidget", u"Differences", None))
        self.hints_label.setText(QCoreApplication.translate("EchoesGameTabWidget", u"<html><head/><body><p align=\"justify\">In\n"
"                                                Metroid Prime 2: Echoes, you can find hints from the\n"
"                                                following sources:</p><p align=\"justify\"><span\n"
"                                                style=\" font-weight:600;\">Sky Temple\n"
"                                                Gateway</span>: Hints for where each of your 9 Sky\n"
"                                                Temple Keys are located. In a Multiworld, describes\n"
"                                                which player has the keys as well.</p><p align=\"justify\"><span\n"
"                                                style=\" font-weight:600;\">Keybearer Corpse</span>:\n"
"                                                Contains a hint for the Flying Ing Cache in the\n"
"                                                associated room for the corpse. This hint will use the\n"
"                                             "
                        "   Broad Category, as described in Hint Item Names.</p><p\n"
"                                                align=\"justify\"><span style=\"\n"
"                                                font-weight:600;\">Luminoth Lore</span>:\n"
"                                                Contains the guaranteed hints and item hints, as\n"
"                                                described next.</p><hr/><p align=\"justify\">In\n"
"                                                each game, each of the following guaranteed hints are\n"
"                                                placed on a luminoth lore scan, placed randomly - this\n"
"                                                means they can be locked behind what they hint for. The\n"
"                                                hints are:</p><p align=\"justify\"><span\n"
"                                                style=\" font-weight:600;\">U-Mos 2</span>:\n"
"                                                The detailed item name of "
                        "what would be Light Suit in\n"
"                                                the vanilla game.</p><p align=\"justify\"><span\n"
"                                                style=\" font-weight:600;\">Dark Temple\n"
"                                                Bosses</span>: The detailed item name which is\n"
"                                                dropped by each of the three temple bosses: Amorbis,\n"
"                                                Chykka and Quadraxis. There's one hint for each boss.</p><p\n"
"                                                align=\"justify\"><span style=\"\n"
"                                                font-weight:600;\">Dark Temple Keys</span>:\n"
"                                                The areas where the temple keys can be located, listed\n"
"                                                in alphabetical order. In multiworld, the area listed\n"
"                                                might be someone else's, but the hint is re"
                        "fering to\n"
"                                                your keys.</p><p align=\"justify\"><span\n"
"                                                style=\" font-weight:600;\">Joke Hints</span>:\n"
"                                                A joke. Uses green text and is a waste of space. There\n"
"                                                are 2 joke hints per game.</p><hr/><p\n"
"                                                align=\"justify\">The remaining Luminoth\n"
"                                                Lores are filled with item hints. These hints are placed\n"
"                                                in three step:</p><p align=\"justify\"><span\n"
"                                                style=\" font-weight:600;\">During Generator</span>:\n"
"                                                Whenever an item is logically placed (see Item Order in\n"
"                                                the spoiler), a hint for that item is placed in a\n"
"        "
                        "                                        compatible lore location - the item location wasn't in\n"
"                                                logic when the given lore was first in logic.</p><p\n"
"                                                align=\"justify\"><span style=\"\n"
"                                                font-weight:600;\">Post Generator</span>:\n"
"                                                When the generator finishes (placed enough items to\n"
"                                                reach credits), lore locations without hints are filled\n"
"                                                in order, starting from these unlocked last. These hints\n"
"                                                will be for items from the Item Order that don't have a\n"
"                                                hint yet, favoring these that have less compatible lore\n"
"                                                locations (should bias for later items in the order).</p><"
                        "p\n"
"                                                align=\"justify\"><span style=\"\n"
"                                                font-weight:600;\">Last Resort</span>: At\n"
"                                                this point, lore locations without a hint get one for a\n"
"                                                random item location.</p><p align=\"justify\">A\n"
"                                                same location can't receive more than one hint from this\n"
"                                                process, ignoring the guaranteed hints.<br/>These\n"
"                                                hints can be in many different formats:</p><p\n"
"                                                align=\"justify\">* Detailed item name with\n"
"                                                detailed room name (x5).<br/>* Precise category\n"
"                                                with detailed room name (x2).<br/>* General\n"
"                               "
                        "                 category with detailed room name (x1).<br/>*\n"
"                                                Detailed item name with only area name (x2).<br/>*\n"
"                                                Precise category with only area name (x1).<br/>*\n"
"                                                Detailed item name, relative to a room with exact\n"
"                                                distance (x1).<br/>* Detailed item name, relative\n"
"                                                to a room with up to distance (x1).<br/>* Detailed\n"
"                                                item name, relative to another precise item name (x1).</p><p\n"
"                                                align=\"justify\">With relative hints,\n"
"                                                distance is measured using the map, not considering\n"
"                                                portals, and is always the shortest path.<br/>For\n"
"                                      "
                        "          hints with two items, the item being hinted is the first\n"
"                                                one.</p></body></html>\n"
"                                            ", None))
        EchoesGameTabWidget.setTabText(EchoesGameTabWidget.indexOf(self.hints_tab), QCoreApplication.translate("EchoesGameTabWidget", u"Hints", None))
        self.hint_item_names_label.setText(QCoreApplication.translate("EchoesGameTabWidget", u"<html><head/><body><p>When\n"
"                                                items are referenced in a hint, multiple names can be\n"
"                                                used depending on how precise the hint is. The names\n"
"                                                each item can use are the following:</p></body></html>\n"
"                                            ", None))
        ___qtablewidgetitem = self.hint_item_names_tree_widget.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("EchoesGameTabWidget", u"Item", None));
        ___qtablewidgetitem1 = self.hint_item_names_tree_widget.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("EchoesGameTabWidget", u"Precise Category", None));
        ___qtablewidgetitem2 = self.hint_item_names_tree_widget.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("EchoesGameTabWidget", u"General Category", None));
        ___qtablewidgetitem3 = self.hint_item_names_tree_widget.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("EchoesGameTabWidget", u"Broad Category", None));
        EchoesGameTabWidget.setTabText(EchoesGameTabWidget.indexOf(self.hint_item_names_tab), QCoreApplication.translate("EchoesGameTabWidget", u"Hint Item Names", None))
        self.hint_locations_label.setText(QCoreApplication.translate("EchoesGameTabWidget", u"<html><head/><body><p>Hints\n"
"                                                are placed in the game by replacing Logbook scans. The\n"
"                                                following are the scans that may have a hint added to\n"
"                                                them:</p></body></html>\n"
"                                            ", None))
        ___qtreewidgetitem = self.hint_locations_tree_widget.headerItem()
        ___qtreewidgetitem.setText(0, QCoreApplication.translate("EchoesGameTabWidget", u"Location", None));
        EchoesGameTabWidget.setTabText(EchoesGameTabWidget.indexOf(self.hint_locations_tab), QCoreApplication.translate("EchoesGameTabWidget", u"Hints Locations", None))
        pass
    # retranslateUi

