# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'games_tab_dread_widget.ui'
##
## Created by: Qt User Interface Compiler version 6.6.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import *  # type: ignore
from PySide6.QtGui import *  # type: ignore
from PySide6.QtWidgets import *  # type: ignore

from randovania.gui.widgets.generate_game_widget import *  # type: ignore

class Ui_DreadGameTabWidget(object):
    def setupUi(self, DreadGameTabWidget):
        if not DreadGameTabWidget.objectName():
            DreadGameTabWidget.setObjectName(u"DreadGameTabWidget")
        DreadGameTabWidget.resize(637, 497)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(DreadGameTabWidget.sizePolicy().hasHeightForWidth())
        DreadGameTabWidget.setSizePolicy(sizePolicy)
        self.tab_intro = QWidget()
        self.tab_intro.setObjectName(u"tab_intro")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.tab_intro.sizePolicy().hasHeightForWidth())
        self.tab_intro.setSizePolicy(sizePolicy1)
        self.intro_layout = QVBoxLayout(self.tab_intro)
        self.intro_layout.setSpacing(6)
        self.intro_layout.setContentsMargins(11, 11, 11, 11)
        self.intro_layout.setObjectName(u"intro_layout")
        self.intro_layout.setSizeConstraint(QLayout.SetMinimumSize)
        self.intro_cover_layout = QHBoxLayout()
        self.intro_cover_layout.setSpacing(6)
        self.intro_cover_layout.setObjectName(u"intro_cover_layout")
        self.game_cover_label = QLabel(self.tab_intro)
        self.game_cover_label.setObjectName(u"game_cover_label")

        self.intro_cover_layout.addWidget(self.game_cover_label)

        self.intro_label = QLabel(self.tab_intro)
        self.intro_label.setObjectName(u"intro_label")
        sizePolicy1.setHeightForWidth(self.intro_label.sizePolicy().hasHeightForWidth())
        self.intro_label.setSizePolicy(sizePolicy1)
        self.intro_label.setWordWrap(True)

        self.intro_cover_layout.addWidget(self.intro_label)


        self.intro_layout.addLayout(self.intro_cover_layout)

        self.quick_generate_button = QPushButton(self.tab_intro)
        self.quick_generate_button.setObjectName(u"quick_generate_button")

        self.intro_layout.addWidget(self.quick_generate_button)

        self.intro_spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.intro_layout.addItem(self.intro_spacer)

        DreadGameTabWidget.addTab(self.tab_intro, "")
        self.tab_generate_game = GenerateGameWidget()
        self.tab_generate_game.setObjectName(u"tab_generate_game")
        DreadGameTabWidget.addTab(self.tab_generate_game, "")
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
        self.faq_scroll_area_contents.setGeometry(QRect(0, 0, 631, 468))
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

        DreadGameTabWidget.addTab(self.faq_tab, "")
        self.differences_tab = QScrollArea()
        self.differences_tab.setObjectName(u"differences_tab")
        self.differences_tab.setWidgetResizable(True)
        self.differences_contents = QWidget()
        self.differences_contents.setObjectName(u"differences_contents")
        self.differences_contents.setGeometry(QRect(0, 0, 631, 468))
        self.verticalLayout = QVBoxLayout(self.differences_contents)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.differences_label = QLabel(self.differences_contents)
        self.differences_label.setObjectName(u"differences_label")
        self.differences_label.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.differences_label.setWordWrap(True)

        self.verticalLayout.addWidget(self.differences_label)

        self.differences_tab.setWidget(self.differences_contents)
        DreadGameTabWidget.addTab(self.differences_tab, "")
        self.known_crashes_tab = QScrollArea()
        self.known_crashes_tab.setObjectName(u"known_crashes_tab")
        self.known_crashes_tab.setWidgetResizable(True)
        self.known_crashes_contents = QWidget()
        self.known_crashes_contents.setObjectName(u"known_crashes_contents")
        self.known_crashes_contents.setGeometry(QRect(0, 0, 617, 544))
        self.known_crashes_layout = QVBoxLayout(self.known_crashes_contents)
        self.known_crashes_layout.setSpacing(6)
        self.known_crashes_layout.setContentsMargins(11, 11, 11, 11)
        self.known_crashes_layout.setObjectName(u"known_crashes_layout")
        self.known_crashes_label = QLabel(self.known_crashes_contents)
        self.known_crashes_label.setObjectName(u"known_crashes_label")
        self.known_crashes_label.setTextFormat(Qt.MarkdownText)
        self.known_crashes_label.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.known_crashes_label.setWordWrap(True)

        self.known_crashes_layout.addWidget(self.known_crashes_label)

        self.known_crashes_tab.setWidget(self.known_crashes_contents)
        DreadGameTabWidget.addTab(self.known_crashes_tab, "")
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
        self.hints_scroll_area_contents.setGeometry(QRect(0, 0, 631, 468))
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

        DreadGameTabWidget.addTab(self.hints_tab, "")
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
        self.hint_item_names_scroll_contents.setGeometry(QRect(0, 0, 631, 468))
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

        DreadGameTabWidget.addTab(self.hint_item_names_tab, "")
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
        self.hint_locations_scroll_contents.setGeometry(QRect(0, 0, 631, 468))
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

        DreadGameTabWidget.addTab(self.hint_locations_tab, "")

        self.retranslateUi(DreadGameTabWidget)

        DreadGameTabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(DreadGameTabWidget)
    # setupUi

    def retranslateUi(self, DreadGameTabWidget):
        self.game_cover_label.setText(QCoreApplication.translate("DreadGameTabWidget", u"TextLabel", None))
        self.intro_label.setText(QCoreApplication.translate("DreadGameTabWidget", u"<html><head/><body><p align=\"justify\">Navigate ZDR, collecting your lost items to cure your &quot;physical amnesia&quot;, and collecting Metroid DNA to complete your transformation into a Metroid before fighting Raven Beak in Itorash.</p><p align=\"justify\">The default settings start with the Pulse Radar - use this to identify hidden blocks if you're unsure where they might be.</p><p align=\"justify\">Raven Beak won't fight you unless you've become sufficiently Metroid - to this end, you'll need to defeat certain major bosses and EMMIs to find Metroid DNA. The default settings require 3 Metroid DNA before Raven Beak will fight you.</p><p align=\"justify\">ADAM stations in Itorash as well as the uppermost part of Dairon will provide hints as to the locations of the Metroid DNA. Other ADAM stations provide generic hints for any items.</p><p align=\"justify\">Don't forget to check out our list of <a href=\"tab://Known Crashes\"><span style=\" text-decoration: underline; color:#007af4;\">known crashes</span></a"
                        ">, as well at the <a href=\"tab://FAQ\"><span style=\" text-decoration: underline; color:#007af4;\">FAQ</span></a>. If you're curious, check the <a href=\"tab://Differences\"><span style=\" text-decoration: underline; color:#007af4;\">differences</span></a> with the original game.</p><p align=\"justify\">To get started, use the Quick Generate button below to generate a game using the default settings!</p></body></html>", None))
        self.quick_generate_button.setText(QCoreApplication.translate("DreadGameTabWidget", u"Quick generate", None))
        DreadGameTabWidget.setTabText(DreadGameTabWidget.indexOf(self.tab_intro), QCoreApplication.translate("DreadGameTabWidget", u"Introduction", None))
        DreadGameTabWidget.setTabText(DreadGameTabWidget.indexOf(self.tab_generate_game), QCoreApplication.translate("DreadGameTabWidget", u"Play", None))
        self.faq_label.setText(QCoreApplication.translate("DreadGameTabWidget", u"# updated from code", None))
        DreadGameTabWidget.setTabText(DreadGameTabWidget.indexOf(self.faq_tab), QCoreApplication.translate("DreadGameTabWidget", u"FAQ", None))
        self.differences_label.setText(QCoreApplication.translate("DreadGameTabWidget", u"<html><head/><body><p>Randovania makes some changes to the original game in order to improve the game experience or to simply fix bugs in the original game.</p><p>Many of these changes are optional and can be disabled in the many options Randovania provides, but the following are <span style=\" font-weight:600;\">always</span> there:</p><ul style=\"margin-top: 0px; margin-bottom: 0px; margin-left: 0px; margin-right: 0px; -qt-list-indent: 1;\"><li style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">White and Yellow EMMis are patrolling their zones by default, with no cutscene based first encounter. Please note this makes where you would first encounter them significantly harder to navigate.</li><li style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Blue and Purple EMMIs do not require the X to be released (Quiet Robe does nothing in the original game!).</li><li style=\" margin"
                        "-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Checkpoints for collecting items in major locations, such as Charge Beam room, were removed in order to avoid softlocks.</li><li style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Raven Beak takes damage consistently between all beams and missiles, in order to not incentivize players to avoid picking an upgrade.</li></ul></body></html>", None))
        DreadGameTabWidget.setTabText(DreadGameTabWidget.indexOf(self.differences_tab), QCoreApplication.translate("DreadGameTabWidget", u"Differences", None))
        self.known_crashes_label.setText(QCoreApplication.translate("DreadGameTabWidget", u"Metroid Dread is known to crash in some circumstances. Make sure to read the following list and how to avoid these.\n"
"\n"
"\n"
"---\n"
"\n"
"\n"
"## After using warp to start in a Save Station.\n"
"\n"
"\n"
"Occasionally after using warp to start, the game crashes at the end of the loading screen. It is not known what circumstances cause the warp to crash.\n"
"\n"
"\n"
"### Workaround\n"
"\n"
"\n"
"Always save before using warp to start so no progression is lost. After the crash, try again.\n"
"\n"
"\n"
"----\n"
"\n"
"## Crash after collecting a suit upgrade\n"
"\n"
"Changing the suit model while a visual effect is present on Samus crashes the game, and the certain room transitions causes the suit model to update.\n"
"\n"
"The following situations are triggers visual effects:\n"
"* Charging a spark or shinesparking.\n"
"* Charging a Power Bomb.\n"
"* Being in a heated/cold room.\n"
"* Using any Aeion ability.\n"
"\n"
"### Workaround\n"
"\n"
"Manually update your suit model by pressing ZL+ZR+D-Pad Up in a kno"
                        "wn safe state.\n"
"\n"
"----\n"
"\n"
"## Random crashes in Ryujinx\n"
"\n"
"\n"
"It has been reported that Metroid Dread in Ryujinx would crash at any point, with no indication, when using the Memory Manager Mode \"Host Unchecked\".\n"
"\n"
"\n"
"### Workaround\n"
"\n"
"\n"
"In Ryujinx configuration, do not use \"Host Unchecked\".\n"
"\n"
"\n"
"----\n"
"\n"
"\n"
"## Crash in Waterfall room in Artaria\n"
"\n"
"\n"
"Rare crashes in the Waterfall room in West Artaria has been reported when playing on console. No reason has been found.\n"
"\n"
"\n"
"### Workaround\n"
"\n"
"\n"
"Save in the Save Station immediately west of Red Teleportal.\n"
"\n"
"", None))
        DreadGameTabWidget.setTabText(DreadGameTabWidget.indexOf(self.known_crashes_tab), QCoreApplication.translate("DreadGameTabWidget", u"Known Crashes", None))
        self.hints_label.setText(QCoreApplication.translate("DreadGameTabWidget", u"<html><head/><body><p align=\"justify\">In Metroid Dread, you can find hints from the following sources:</p><p align=\"justify\"><span style=\" font-weight:600;\">Network Station</span>: Contains one unique item hint per station. A single item can't be hinted twice by two network stations.</p><p align=\"justify\"><span style=\" font-weight:600;\">Dairon - Navigation Station North</span>: ADAM will provide a hint to the locations of all Metroid DNA.</p><p align=\"justify\"><span style=\" font-weight:600;\">Itorash</span>: A new Navigation Station has been added to the elevator room. ADAM will provide a hint to the locations of all Metroid DNA.</p><hr/><p align=\"justify\">For more details with how hints are assigned, check Metroid Prime 2: Echoes page. Hints assigned to Network Stations follow the same logic as item hints assigned to Luminoth Lore.</p></body></html>", None))
        DreadGameTabWidget.setTabText(DreadGameTabWidget.indexOf(self.hints_tab), QCoreApplication.translate("DreadGameTabWidget", u"Hints", None))
        self.hint_item_names_label.setText(QCoreApplication.translate("DreadGameTabWidget", u"<html><head/><body><p>When items are referenced in a hint, multiple names can be used depending on how precise the hint is. These additional names are not used by hints in Metroid Dread, but can be used if hinted by another game such as Metroid Prime 2: Echoes.</p><p>The names each item can use are the following: </p></body></html>", None))
        ___qtablewidgetitem = self.hint_item_names_tree_widget.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("DreadGameTabWidget", u"Item", None));
        ___qtablewidgetitem1 = self.hint_item_names_tree_widget.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("DreadGameTabWidget", u"Precise Category", None));
        ___qtablewidgetitem2 = self.hint_item_names_tree_widget.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("DreadGameTabWidget", u"General Category", None));
        ___qtablewidgetitem3 = self.hint_item_names_tree_widget.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("DreadGameTabWidget", u"Broad Category", None));
        DreadGameTabWidget.setTabText(DreadGameTabWidget.indexOf(self.hint_item_names_tab), QCoreApplication.translate("DreadGameTabWidget", u"Hint Item Names", None))
        self.hint_locations_label.setText(QCoreApplication.translate("DreadGameTabWidget", u"<html><head/><body><p>Hints are placed in the game by replacing the ADAM briefings in the Navigation Stations. The following are the areas that have a hint added to them: </p></body></html>", None))
        ___qtreewidgetitem = self.hint_locations_tree_widget.headerItem()
        ___qtreewidgetitem.setText(0, QCoreApplication.translate("DreadGameTabWidget", u"Location", None));
        DreadGameTabWidget.setTabText(DreadGameTabWidget.indexOf(self.hint_locations_tab), QCoreApplication.translate("DreadGameTabWidget", u"Hints Locations", None))
        pass
    # retranslateUi

