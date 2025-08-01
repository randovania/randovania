# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'games_tab_fusion_widget.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QAbstractScrollArea, QApplication, QFrame,
    QGridLayout, QHBoxLayout, QHeaderView, QLabel,
    QPushButton, QScrollArea, QSizePolicy, QSpacerItem,
    QTabWidget, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QWidget)

from randovania.gui.widgets.generate_game_widget import GenerateGameWidget
from randovania.gui.widgets.hint_feature_tab import (LocationHintFeatureTab, PickupHintFeatureTab)

class Ui_FusionGameTabWidget(object):
    def setupUi(self, FusionGameTabWidget):
        if not FusionGameTabWidget.objectName():
            FusionGameTabWidget.setObjectName(u"FusionGameTabWidget")
        FusionGameTabWidget.resize(698, 453)
        FusionGameTabWidget.setDocumentMode(True)
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

        FusionGameTabWidget.addTab(self.tab_intro, "")
        self.tab_generate_game = GenerateGameWidget()
        self.tab_generate_game.setObjectName(u"tab_generate_game")
        FusionGameTabWidget.addTab(self.tab_generate_game, "")
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
        self.faq_scroll_area_contents.setGeometry(QRect(0, 0, 696, 423))
        self.faq_scroll_layout = QGridLayout(self.faq_scroll_area_contents)
        self.faq_scroll_layout.setSpacing(6)
        self.faq_scroll_layout.setContentsMargins(11, 11, 11, 11)
        self.faq_scroll_layout.setObjectName(u"faq_scroll_layout")
        self.faq_label = QLabel(self.faq_scroll_area_contents)
        self.faq_label.setObjectName(u"faq_label")
        self.faq_label.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.faq_label.setWordWrap(True)

        self.faq_scroll_layout.addWidget(self.faq_label, 0, 0, 1, 1)

        self.faq_scroll_area.setWidget(self.faq_scroll_area_contents)

        self.faq_layout.addWidget(self.faq_scroll_area, 0, 0, 1, 1)

        FusionGameTabWidget.addTab(self.faq_tab, "")
        self.differences_tab = QWidget()
        self.differences_tab.setObjectName(u"differences_tab")
        self.verticalLayout_2 = QVBoxLayout(self.differences_tab)
        self.verticalLayout_2.setSpacing(6)
        self.verticalLayout_2.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.differences_scroll_area = QScrollArea(self.differences_tab)
        self.differences_scroll_area.setObjectName(u"differences_scroll_area")
        self.differences_scroll_area.setWidgetResizable(True)
        self.differences_scroll_contents = QWidget()
        self.differences_scroll_contents.setObjectName(u"differences_scroll_contents")
        self.differences_scroll_contents.setGeometry(QRect(0, -616, 664, 1021))
        self.verticalLayout = QVBoxLayout(self.differences_scroll_contents)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.differences_label = QLabel(self.differences_scroll_contents)
        self.differences_label.setObjectName(u"differences_label")
        self.differences_label.setTextFormat(Qt.MarkdownText)
        self.differences_label.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.differences_label.setWordWrap(True)

        self.verticalLayout.addWidget(self.differences_label)

        self.differences_scroll_area.setWidget(self.differences_scroll_contents)

        self.verticalLayout_2.addWidget(self.differences_scroll_area)

        FusionGameTabWidget.addTab(self.differences_tab, "")
        self.hints_tab = QWidget()
        self.hints_tab.setObjectName(u"hints_tab")
        self.hints_tab_layout_4 = QVBoxLayout(self.hints_tab)
        self.hints_tab_layout_4.setSpacing(0)
        self.hints_tab_layout_4.setContentsMargins(11, 11, 11, 11)
        self.hints_tab_layout_4.setObjectName(u"hints_tab_layout_4")
        self.hints_tab_layout_4.setContentsMargins(0, 0, 0, 0)
        self.hints_scroll_area = QScrollArea(self.hints_tab)
        self.hints_scroll_area.setObjectName(u"hints_scroll_area")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.hints_scroll_area.sizePolicy().hasHeightForWidth())
        self.hints_scroll_area.setSizePolicy(sizePolicy)
        self.hints_scroll_area.setWidgetResizable(True)
        self.hints_scroll_area_contents = QWidget()
        self.hints_scroll_area_contents.setObjectName(u"hints_scroll_area_contents")
        self.hints_scroll_area_contents.setGeometry(QRect(0, 0, 682, 685))
        sizePolicy.setHeightForWidth(self.hints_scroll_area_contents.sizePolicy().hasHeightForWidth())
        self.hints_scroll_area_contents.setSizePolicy(sizePolicy)
        self.hints_scroll_layout_4 = QVBoxLayout(self.hints_scroll_area_contents)
        self.hints_scroll_layout_4.setSpacing(6)
        self.hints_scroll_layout_4.setContentsMargins(11, 11, 11, 11)
        self.hints_scroll_layout_4.setObjectName(u"hints_scroll_layout_4")
        self.hints_scroll_layout_4.setContentsMargins(-1, 6, 6, 6)
        self.hints_label = QLabel(self.hints_scroll_area_contents)
        self.hints_label.setObjectName(u"hints_label")
        sizePolicy.setHeightForWidth(self.hints_label.sizePolicy().hasHeightForWidth())
        self.hints_label.setSizePolicy(sizePolicy)
        self.hints_label.setTextFormat(Qt.MarkdownText)
        self.hints_label.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.hints_label.setWordWrap(True)

        self.hints_scroll_layout_4.addWidget(self.hints_label)

        self.tableWidget = QTableWidget(self.hints_scroll_area_contents)
        if (self.tableWidget.columnCount() < 4):
            self.tableWidget.setColumnCount(4)
        font = QFont()
        font.setBold(True)
        __qtablewidgetitem = QTableWidgetItem()
        __qtablewidgetitem.setFont(font);
        self.tableWidget.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        __qtablewidgetitem1.setFont(font);
        self.tableWidget.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        __qtablewidgetitem3.setFont(font);
        self.tableWidget.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        if (self.tableWidget.rowCount() < 11):
            self.tableWidget.setRowCount(11)
        __qtablewidgetitem4 = QTableWidgetItem()
        self.tableWidget.setVerticalHeaderItem(0, __qtablewidgetitem4)
        __qtablewidgetitem5 = QTableWidgetItem()
        self.tableWidget.setVerticalHeaderItem(1, __qtablewidgetitem5)
        __qtablewidgetitem6 = QTableWidgetItem()
        self.tableWidget.setVerticalHeaderItem(2, __qtablewidgetitem6)
        __qtablewidgetitem7 = QTableWidgetItem()
        self.tableWidget.setVerticalHeaderItem(3, __qtablewidgetitem7)
        __qtablewidgetitem8 = QTableWidgetItem()
        self.tableWidget.setVerticalHeaderItem(4, __qtablewidgetitem8)
        __qtablewidgetitem9 = QTableWidgetItem()
        self.tableWidget.setVerticalHeaderItem(5, __qtablewidgetitem9)
        __qtablewidgetitem10 = QTableWidgetItem()
        self.tableWidget.setVerticalHeaderItem(6, __qtablewidgetitem10)
        __qtablewidgetitem11 = QTableWidgetItem()
        self.tableWidget.setVerticalHeaderItem(7, __qtablewidgetitem11)
        __qtablewidgetitem12 = QTableWidgetItem()
        self.tableWidget.setVerticalHeaderItem(8, __qtablewidgetitem12)
        __qtablewidgetitem13 = QTableWidgetItem()
        self.tableWidget.setVerticalHeaderItem(9, __qtablewidgetitem13)
        __qtablewidgetitem14 = QTableWidgetItem()
        self.tableWidget.setVerticalHeaderItem(10, __qtablewidgetitem14)
        __qtablewidgetitem15 = QTableWidgetItem()
        self.tableWidget.setItem(0, 0, __qtablewidgetitem15)
        __qtablewidgetitem16 = QTableWidgetItem()
        self.tableWidget.setItem(0, 1, __qtablewidgetitem16)
        __qtablewidgetitem17 = QTableWidgetItem()
        self.tableWidget.setItem(0, 2, __qtablewidgetitem17)
        __qtablewidgetitem18 = QTableWidgetItem()
        self.tableWidget.setItem(0, 3, __qtablewidgetitem18)
        __qtablewidgetitem19 = QTableWidgetItem()
        self.tableWidget.setItem(1, 0, __qtablewidgetitem19)
        __qtablewidgetitem20 = QTableWidgetItem()
        self.tableWidget.setItem(1, 1, __qtablewidgetitem20)
        __qtablewidgetitem21 = QTableWidgetItem()
        self.tableWidget.setItem(1, 2, __qtablewidgetitem21)
        __qtablewidgetitem22 = QTableWidgetItem()
        self.tableWidget.setItem(1, 3, __qtablewidgetitem22)
        __qtablewidgetitem23 = QTableWidgetItem()
        self.tableWidget.setItem(2, 0, __qtablewidgetitem23)
        __qtablewidgetitem24 = QTableWidgetItem()
        self.tableWidget.setItem(2, 1, __qtablewidgetitem24)
        __qtablewidgetitem25 = QTableWidgetItem()
        self.tableWidget.setItem(2, 2, __qtablewidgetitem25)
        __qtablewidgetitem26 = QTableWidgetItem()
        self.tableWidget.setItem(2, 3, __qtablewidgetitem26)
        __qtablewidgetitem27 = QTableWidgetItem()
        self.tableWidget.setItem(3, 0, __qtablewidgetitem27)
        __qtablewidgetitem28 = QTableWidgetItem()
        self.tableWidget.setItem(3, 1, __qtablewidgetitem28)
        __qtablewidgetitem29 = QTableWidgetItem()
        self.tableWidget.setItem(3, 2, __qtablewidgetitem29)
        __qtablewidgetitem30 = QTableWidgetItem()
        self.tableWidget.setItem(3, 3, __qtablewidgetitem30)
        __qtablewidgetitem31 = QTableWidgetItem()
        self.tableWidget.setItem(4, 0, __qtablewidgetitem31)
        __qtablewidgetitem32 = QTableWidgetItem()
        self.tableWidget.setItem(4, 1, __qtablewidgetitem32)
        __qtablewidgetitem33 = QTableWidgetItem()
        self.tableWidget.setItem(4, 2, __qtablewidgetitem33)
        __qtablewidgetitem34 = QTableWidgetItem()
        self.tableWidget.setItem(4, 3, __qtablewidgetitem34)
        __qtablewidgetitem35 = QTableWidgetItem()
        self.tableWidget.setItem(5, 0, __qtablewidgetitem35)
        __qtablewidgetitem36 = QTableWidgetItem()
        self.tableWidget.setItem(5, 1, __qtablewidgetitem36)
        __qtablewidgetitem37 = QTableWidgetItem()
        self.tableWidget.setItem(5, 2, __qtablewidgetitem37)
        __qtablewidgetitem38 = QTableWidgetItem()
        self.tableWidget.setItem(5, 3, __qtablewidgetitem38)
        __qtablewidgetitem39 = QTableWidgetItem()
        self.tableWidget.setItem(6, 0, __qtablewidgetitem39)
        __qtablewidgetitem40 = QTableWidgetItem()
        self.tableWidget.setItem(6, 1, __qtablewidgetitem40)
        __qtablewidgetitem41 = QTableWidgetItem()
        self.tableWidget.setItem(6, 2, __qtablewidgetitem41)
        __qtablewidgetitem42 = QTableWidgetItem()
        self.tableWidget.setItem(6, 3, __qtablewidgetitem42)
        __qtablewidgetitem43 = QTableWidgetItem()
        self.tableWidget.setItem(7, 0, __qtablewidgetitem43)
        __qtablewidgetitem44 = QTableWidgetItem()
        self.tableWidget.setItem(7, 1, __qtablewidgetitem44)
        __qtablewidgetitem45 = QTableWidgetItem()
        self.tableWidget.setItem(7, 2, __qtablewidgetitem45)
        __qtablewidgetitem46 = QTableWidgetItem()
        self.tableWidget.setItem(7, 3, __qtablewidgetitem46)
        __qtablewidgetitem47 = QTableWidgetItem()
        self.tableWidget.setItem(8, 0, __qtablewidgetitem47)
        __qtablewidgetitem48 = QTableWidgetItem()
        self.tableWidget.setItem(8, 1, __qtablewidgetitem48)
        __qtablewidgetitem49 = QTableWidgetItem()
        self.tableWidget.setItem(8, 2, __qtablewidgetitem49)
        __qtablewidgetitem50 = QTableWidgetItem()
        self.tableWidget.setItem(8, 3, __qtablewidgetitem50)
        __qtablewidgetitem51 = QTableWidgetItem()
        self.tableWidget.setItem(9, 0, __qtablewidgetitem51)
        __qtablewidgetitem52 = QTableWidgetItem()
        self.tableWidget.setItem(9, 1, __qtablewidgetitem52)
        __qtablewidgetitem53 = QTableWidgetItem()
        self.tableWidget.setItem(9, 2, __qtablewidgetitem53)
        __qtablewidgetitem54 = QTableWidgetItem()
        self.tableWidget.setItem(9, 3, __qtablewidgetitem54)
        __qtablewidgetitem55 = QTableWidgetItem()
        self.tableWidget.setItem(10, 0, __qtablewidgetitem55)
        __qtablewidgetitem56 = QTableWidgetItem()
        self.tableWidget.setItem(10, 1, __qtablewidgetitem56)
        __qtablewidgetitem57 = QTableWidgetItem()
        self.tableWidget.setItem(10, 2, __qtablewidgetitem57)
        __qtablewidgetitem58 = QTableWidgetItem()
        self.tableWidget.setItem(10, 3, __qtablewidgetitem58)
        self.tableWidget.setObjectName(u"tableWidget")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.tableWidget.sizePolicy().hasHeightForWidth())
        self.tableWidget.setSizePolicy(sizePolicy1)
        self.tableWidget.setMinimumSize(QSize(400, 0))
        self.tableWidget.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.tableWidget.setAutoScroll(True)
        self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableWidget.setRowCount(11)
        self.tableWidget.setColumnCount(4)
        self.tableWidget.horizontalHeader().setVisible(True)
        self.tableWidget.horizontalHeader().setCascadingSectionResizes(False)
        self.tableWidget.horizontalHeader().setMinimumSectionSize(50)
        self.tableWidget.horizontalHeader().setDefaultSectionSize(150)
        self.tableWidget.verticalHeader().setVisible(False)
        self.tableWidget.verticalHeader().setDefaultSectionSize(30)

        self.hints_scroll_layout_4.addWidget(self.tableWidget)

        self.line = QFrame(self.hints_scroll_area_contents)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.hints_scroll_layout_4.addWidget(self.line)

        self.label = QLabel(self.hints_scroll_area_contents)
        self.label.setObjectName(u"label")
        self.label.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.label.setWordWrap(True)

        self.hints_scroll_layout_4.addWidget(self.label)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.hints_scroll_layout_4.addItem(self.verticalSpacer)

        self.hints_scroll_area.setWidget(self.hints_scroll_area_contents)

        self.hints_tab_layout_4.addWidget(self.hints_scroll_area)

        FusionGameTabWidget.addTab(self.hints_tab, "")
        self.pickup_hint_features_tab = PickupHintFeatureTab()
        self.pickup_hint_features_tab.setObjectName(u"pickup_hint_features_tab")
        self.hint_item_names_layout_4 = QVBoxLayout(self.pickup_hint_features_tab)
        self.hint_item_names_layout_4.setSpacing(0)
        self.hint_item_names_layout_4.setContentsMargins(11, 11, 11, 11)
        self.hint_item_names_layout_4.setObjectName(u"hint_item_names_layout_4")
        self.hint_item_names_layout_4.setContentsMargins(0, 0, 0, 0)
        FusionGameTabWidget.addTab(self.pickup_hint_features_tab, "")
        self.location_hint_features_tab = LocationHintFeatureTab()
        self.location_hint_features_tab.setObjectName(u"location_hint_features_tab")
        FusionGameTabWidget.addTab(self.location_hint_features_tab, "")

        self.retranslateUi(FusionGameTabWidget)

        FusionGameTabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(FusionGameTabWidget)
    # setupUi

    def retranslateUi(self, FusionGameTabWidget):
        self.game_cover_label.setText(QCoreApplication.translate("FusionGameTabWidget", u"TextLabel", None))
        self.intro_label.setText(QCoreApplication.translate("FusionGameTabWidget", u"<html><head/><body><p align=\"justify\">Explore the B.S.L Station, collect the escaped Infant Metroids, all while gearing up to fight the SA-X before destroying the station!</p><p align=\"justify\">To aid Samus on her journey, ADAM now provides hints at Navigation Stations, this is explained further on the <a href=\"tab://Hints\"><span style=\" text-decoration: underline; color:#007af4;\">Hints</span></a> Tabs.</p><p align=\"justify\">For more details, checkout the <a href=\"tab://FAQ\"><span style=\" text-decoration: underline; color:#007af4;\">FAQ</span></a> and <a href=\"tab://Differences\"><span style=\" text-decoration: underline; color:#007af4;\">Differences</span></a> tabs.</p><p align=\"justify\">To get started, use the Quick Generate button to generate a game using the default and recommended settings.</p></body></html>", None))
        self.quick_generate_button.setText(QCoreApplication.translate("FusionGameTabWidget", u"Quick generate", None))
        FusionGameTabWidget.setTabText(FusionGameTabWidget.indexOf(self.tab_intro), QCoreApplication.translate("FusionGameTabWidget", u"Introduction", None))
        FusionGameTabWidget.setTabText(FusionGameTabWidget.indexOf(self.tab_generate_game), QCoreApplication.translate("FusionGameTabWidget", u"Play", None))
        self.faq_label.setText(QCoreApplication.translate("FusionGameTabWidget", u"# updated from code", None))
        FusionGameTabWidget.setTabText(FusionGameTabWidget.indexOf(self.faq_tab), QCoreApplication.translate("FusionGameTabWidget", u"FAQ", None))
        self.differences_label.setText(QCoreApplication.translate("FusionGameTabWidget", u"Randovania and the MARS patcher make some changes to the original game in order to improve the randomizer experience or to simply fix bugs in the original game. Key differences are: \n"
"\n"
"### Gameplay\n"
"\n"
"- Added Pickups to the following Areas:\n"
"    - Main Deck - Habitation Deck (Save the Animals)\n"
"    - Main Deck - Auxiliary Power\n"
"    - Main Deck - Sub-Zero Containment (near Ridley statue)\n"
"    - Main Deck - Quarantine Bay\n"
"    - Sector 1 (SRX) - Atmospheric Stabilizer Northeast\n"
"    - Sector 3 (PYR) - Main Boiler Control Room\n"
"\n"
"- Security Keycards are now shuffleable items and Security Rooms are viable pickup locations.\n"
"\n"
"- The vanilla event system has been replaced with a non-linear one.\n"
"\n"
"- Missiles, Beams, and Suit upgrades have been split. More details found on the FAQ tab.\n"
"\n"
"- Screw Attack will no longer allow Single Wall Jumps. Wall Jump behaviour is now the same as without Screw Attack. \n"
"\n"
"- Red X drop chances have been slightly increased."
                        " Red X drops are now guaranteed when both Health and Missiles are full to help replenish Power Bombs.\n"
"\n"
"- Hints have been placed at Navigation Stations. More details found on the Hints tab.\n"
"\n"
"- In order to fight the SA-X, you will need to collect a configurable amount of infant Metroids, a way to approach the door to the Operations Room, Charge Beam and Missiles. Plasma Beam is not required to defeat the SA-X, and the Level 4 Keycard is not required to go to the Operations Room.\n"
"\n"
"- During the escape, hatches no longer lock and the timer only activates upon entering the hangar to fight the Omega Metroid.\n"
"\n"
"### Room Changes\n"
"\n"
"- Main Deck - Operations Room - now a grey Level 0 hatch, this means the Level 4 Keycard may not be required to beat the game.\n"
"\n"
"- Main Deck - Operations Ventilation - repaired the connection between Crew Quarters East and West.\n"
"\n"
"- Main Deck - Silo Entry - the Zoro cocoon is moved to allow traversal.\n"
"\n"
"- Main Deck - Central Reactor C"
                        "ore - now has a platform near the top to make traversal still possible after the vines have been removed.\n"
"\n"
"- Sector 2 - Ripper Tower - now always has an open hatch.\n"
"\n"
"- Sector 2 - Overgrown Spire - added blocks to the climb to allow traversal after the vines are removed, which are speed blocks to maintain vanilla room strategies.\n"
"\n"
"- Sector 5 - The destruction of Sector 5 has been changed to always be consistent. Everything in West Sector 5 will always be undamaged, while everything East will be destroyed.\n"
"\n"
"- Sector 5 - Arctic Containment - The red Level 4 hatch between Arctic Containment and Crows Nest has been changed to a yellow Level 3 hatch.\n"
"\n"
"- Sector 5 - Ripper Road - now always has an open hatch.\n"
"\n"
"- Sector 6 - Weapons Testing Grounds - The Power Bomb wall that the SA-X destroys is permanently destroyed.\n"
"\n"
"- Made several enemy spawns consistent.\n"
"\n"
"### Quality of Life\n"
"\n"
"- You can now warp to start by pressing L on the map screen. All progr"
                        "ess since your last save will be lost. This is NEVER considered logical.\n"
"\n"
"- On the inventory screen, you can now enable/disable acquired powerups. Infant Metroid count is also displayed.\n"
"\n"
"- On the map screen, you can now cycle the Sectors on the map by pressing SELECT and show the current room name by pressing A. In-game Time (IGT) and Level 0 security status is also displayed.\n"
"\n"
"- The minimap has various bugfixes and new sector indicators are added to the sector transitions.\n"
"\n"
"- A cosmetic setting has been added to reveal all hidden blocks and pillars.\n"
"\n"
"- Some sprite variants have been modified for accessibility purposes.", None))
        FusionGameTabWidget.setTabText(FusionGameTabWidget.indexOf(self.differences_tab), QCoreApplication.translate("FusionGameTabWidget", u"Differences", None))
        self.hints_label.setText(QCoreApplication.translate("FusionGameTabWidget", u"<html><head/><body><p>In Metroid Fusion, players can find hints at the various Navigation Terminals spread throught the B.S.L. The Navigation Terminals are unlocked by the various Keycard pickups, and the graphics on the terminal can be used to identify which is needed in-game. There are three main types of hints: </p><p>1) <span style=\" font-weight:700;\">Infant Metroids</span>: The Restricted Labs and Operations Deck Navigation Rooms give a hint where the Infant Metroids can be found. Metroids on Bosses will be hinted on Operations Deck, and any remaining Metroids around the station will be hinted on Restricted Labs.</p><p>2) <span style=\" font-weight:700;\">Charge Beam</span>: The Auxiliary Navigation Terminal always gives a hint where the Charge Beam can be found. </p><p>3) <span style=\" font-weight:700;\">Regular: </span>The remaining Navigation Terminals give hints to random pickups with varying precision. One of these hints will randomly be replaced by a joke hint, which will have green text and a fu"
                        "nny message to the player.</p><p>The table below summarizes the above:</p></body></html>", None))
        ___qtablewidgetitem = self.tableWidget.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("FusionGameTabWidget", u"Region", None));
        ___qtablewidgetitem1 = self.tableWidget.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("FusionGameTabWidget", u"Area", None));
        ___qtablewidgetitem2 = self.tableWidget.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("FusionGameTabWidget", u"Lock", None));
        ___qtablewidgetitem3 = self.tableWidget.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("FusionGameTabWidget", u"Hint Type", None));
        ___qtablewidgetitem4 = self.tableWidget.verticalHeaderItem(0)
        ___qtablewidgetitem4.setText(QCoreApplication.translate("FusionGameTabWidget", u"New Row", None));
        ___qtablewidgetitem5 = self.tableWidget.verticalHeaderItem(1)
        ___qtablewidgetitem5.setText(QCoreApplication.translate("FusionGameTabWidget", u"New Row", None));
        ___qtablewidgetitem6 = self.tableWidget.verticalHeaderItem(2)
        ___qtablewidgetitem6.setText(QCoreApplication.translate("FusionGameTabWidget", u"New Row", None));
        ___qtablewidgetitem7 = self.tableWidget.verticalHeaderItem(3)
        ___qtablewidgetitem7.setText(QCoreApplication.translate("FusionGameTabWidget", u"New Row", None));
        ___qtablewidgetitem8 = self.tableWidget.verticalHeaderItem(4)
        ___qtablewidgetitem8.setText(QCoreApplication.translate("FusionGameTabWidget", u"New Row", None));
        ___qtablewidgetitem9 = self.tableWidget.verticalHeaderItem(5)
        ___qtablewidgetitem9.setText(QCoreApplication.translate("FusionGameTabWidget", u"New Row", None));
        ___qtablewidgetitem10 = self.tableWidget.verticalHeaderItem(6)
        ___qtablewidgetitem10.setText(QCoreApplication.translate("FusionGameTabWidget", u"New Row", None));
        ___qtablewidgetitem11 = self.tableWidget.verticalHeaderItem(7)
        ___qtablewidgetitem11.setText(QCoreApplication.translate("FusionGameTabWidget", u"New Row", None));
        ___qtablewidgetitem12 = self.tableWidget.verticalHeaderItem(8)
        ___qtablewidgetitem12.setText(QCoreApplication.translate("FusionGameTabWidget", u"New Row", None));
        ___qtablewidgetitem13 = self.tableWidget.verticalHeaderItem(9)
        ___qtablewidgetitem13.setText(QCoreApplication.translate("FusionGameTabWidget", u"New Row", None));
        ___qtablewidgetitem14 = self.tableWidget.verticalHeaderItem(10)
        ___qtablewidgetitem14.setText(QCoreApplication.translate("FusionGameTabWidget", u"New Row", None));

        __sortingEnabled = self.tableWidget.isSortingEnabled()
        self.tableWidget.setSortingEnabled(False)
        ___qtablewidgetitem15 = self.tableWidget.item(0, 0)
        ___qtablewidgetitem15.setText(QCoreApplication.translate("FusionGameTabWidget", u"Main Deck", None));
        ___qtablewidgetitem16 = self.tableWidget.item(0, 1)
        ___qtablewidgetitem16.setText(QCoreApplication.translate("FusionGameTabWidget", u"Auxiliary Navigation Room", None));
        ___qtablewidgetitem17 = self.tableWidget.item(0, 2)
        ___qtablewidgetitem17.setText(QCoreApplication.translate("FusionGameTabWidget", u"Unlocked", None));
        ___qtablewidgetitem18 = self.tableWidget.item(0, 3)
        ___qtablewidgetitem18.setText(QCoreApplication.translate("FusionGameTabWidget", u"Specific Charge Beam, Configurable Precision", None));
        ___qtablewidgetitem19 = self.tableWidget.item(1, 0)
        ___qtablewidgetitem19.setText(QCoreApplication.translate("FusionGameTabWidget", u"Main Deck", None));
        ___qtablewidgetitem20 = self.tableWidget.item(1, 1)
        ___qtablewidgetitem20.setText(QCoreApplication.translate("FusionGameTabWidget", u"Crew Quarters Navigation Room", None));
        ___qtablewidgetitem21 = self.tableWidget.item(1, 2)
        ___qtablewidgetitem21.setText(QCoreApplication.translate("FusionGameTabWidget", u"Level 1 Keycard (BLUE)", None));
        ___qtablewidgetitem22 = self.tableWidget.item(1, 3)
        ___qtablewidgetitem22.setText(QCoreApplication.translate("FusionGameTabWidget", u"Regular Hint, Featural", None));
        ___qtablewidgetitem23 = self.tableWidget.item(2, 0)
        ___qtablewidgetitem23.setText(QCoreApplication.translate("FusionGameTabWidget", u"Main Deck", None));
        ___qtablewidgetitem24 = self.tableWidget.item(2, 1)
        ___qtablewidgetitem24.setText(QCoreApplication.translate("FusionGameTabWidget", u"Nexus Navigation Room", None));
        ___qtablewidgetitem25 = self.tableWidget.item(2, 2)
        ___qtablewidgetitem25.setText(QCoreApplication.translate("FusionGameTabWidget", u"Level 4 Keycard (RED)", None));
        ___qtablewidgetitem26 = self.tableWidget.item(2, 3)
        ___qtablewidgetitem26.setText(QCoreApplication.translate("FusionGameTabWidget", u"Regular Hint, Featural", None));
        ___qtablewidgetitem27 = self.tableWidget.item(3, 0)
        ___qtablewidgetitem27.setText(QCoreApplication.translate("FusionGameTabWidget", u"Main Deck", None));
        ___qtablewidgetitem28 = self.tableWidget.item(3, 1)
        ___qtablewidgetitem28.setText(QCoreApplication.translate("FusionGameTabWidget", u"Operations Deck Navigation Room", None));
        ___qtablewidgetitem29 = self.tableWidget.item(3, 2)
        ___qtablewidgetitem29.setText(QCoreApplication.translate("FusionGameTabWidget", u"Level 1 Keycard (BLUE)", None));
        ___qtablewidgetitem30 = self.tableWidget.item(3, 3)
        ___qtablewidgetitem30.setText(QCoreApplication.translate("FusionGameTabWidget", u"Specific Infant Metroids, Configurable Precision", None));
        ___qtablewidgetitem31 = self.tableWidget.item(4, 0)
        ___qtablewidgetitem31.setText(QCoreApplication.translate("FusionGameTabWidget", u"Main Deck", None));
        ___qtablewidgetitem32 = self.tableWidget.item(4, 1)
        ___qtablewidgetitem32.setText(QCoreApplication.translate("FusionGameTabWidget", u"Restricted Navigation Room", None));
        ___qtablewidgetitem33 = self.tableWidget.item(4, 2)
        ___qtablewidgetitem33.setText(QCoreApplication.translate("FusionGameTabWidget", u"Level 4 Keycard (RED)", None));
        ___qtablewidgetitem34 = self.tableWidget.item(4, 3)
        ___qtablewidgetitem34.setText(QCoreApplication.translate("FusionGameTabWidget", u"Specific Infant Metroids, Configurable Precision", None));
        ___qtablewidgetitem35 = self.tableWidget.item(5, 0)
        ___qtablewidgetitem35.setText(QCoreApplication.translate("FusionGameTabWidget", u"Sector 1 (SRX)", None));
        ___qtablewidgetitem36 = self.tableWidget.item(5, 1)
        ___qtablewidgetitem36.setText(QCoreApplication.translate("FusionGameTabWidget", u"Entrance Navigation Room", None));
        ___qtablewidgetitem37 = self.tableWidget.item(5, 2)
        ___qtablewidgetitem37.setText(QCoreApplication.translate("FusionGameTabWidget", u"Level 2 Keycard (GREEN)", None));
        ___qtablewidgetitem38 = self.tableWidget.item(5, 3)
        ___qtablewidgetitem38.setText(QCoreApplication.translate("FusionGameTabWidget", u"Regular Hint, Featural", None));
        ___qtablewidgetitem39 = self.tableWidget.item(6, 0)
        ___qtablewidgetitem39.setText(QCoreApplication.translate("FusionGameTabWidget", u"Sector 2 (TRO)", None));
        ___qtablewidgetitem40 = self.tableWidget.item(6, 1)
        ___qtablewidgetitem40.setText(QCoreApplication.translate("FusionGameTabWidget", u"Entrance Navigation Room", None));
        ___qtablewidgetitem41 = self.tableWidget.item(6, 2)
        ___qtablewidgetitem41.setText(QCoreApplication.translate("FusionGameTabWidget", u"Level 2 Keycard (GREEN)", None));
        ___qtablewidgetitem42 = self.tableWidget.item(6, 3)
        ___qtablewidgetitem42.setText(QCoreApplication.translate("FusionGameTabWidget", u"Regular Hint, Featural", None));
        ___qtablewidgetitem43 = self.tableWidget.item(7, 0)
        ___qtablewidgetitem43.setText(QCoreApplication.translate("FusionGameTabWidget", u"Sector 3 (PYR)", None));
        ___qtablewidgetitem44 = self.tableWidget.item(7, 1)
        ___qtablewidgetitem44.setText(QCoreApplication.translate("FusionGameTabWidget", u"Entrance Navigation Room", None));
        ___qtablewidgetitem45 = self.tableWidget.item(7, 2)
        ___qtablewidgetitem45.setText(QCoreApplication.translate("FusionGameTabWidget", u"Level 3 Keycard (YELLOW)", None));
        ___qtablewidgetitem46 = self.tableWidget.item(7, 3)
        ___qtablewidgetitem46.setText(QCoreApplication.translate("FusionGameTabWidget", u"Regular Hint, Featural", None));
        ___qtablewidgetitem47 = self.tableWidget.item(8, 0)
        ___qtablewidgetitem47.setText(QCoreApplication.translate("FusionGameTabWidget", u"Sector 4 (AQA)", None));
        ___qtablewidgetitem48 = self.tableWidget.item(8, 1)
        ___qtablewidgetitem48.setText(QCoreApplication.translate("FusionGameTabWidget", u"Entrance Navigation Room", None));
        ___qtablewidgetitem49 = self.tableWidget.item(8, 2)
        ___qtablewidgetitem49.setText(QCoreApplication.translate("FusionGameTabWidget", u"Level 3 Keycard (YELLOW)", None));
        ___qtablewidgetitem50 = self.tableWidget.item(8, 3)
        ___qtablewidgetitem50.setText(QCoreApplication.translate("FusionGameTabWidget", u"Regular Hint, Featural", None));
        ___qtablewidgetitem51 = self.tableWidget.item(9, 0)
        ___qtablewidgetitem51.setText(QCoreApplication.translate("FusionGameTabWidget", u"Sector 5 (ARC)", None));
        ___qtablewidgetitem52 = self.tableWidget.item(9, 1)
        ___qtablewidgetitem52.setText(QCoreApplication.translate("FusionGameTabWidget", u"Entrance Navigation Room", None));
        ___qtablewidgetitem53 = self.tableWidget.item(9, 2)
        ___qtablewidgetitem53.setText(QCoreApplication.translate("FusionGameTabWidget", u"Level 4 Keycard (RED)", None));
        ___qtablewidgetitem54 = self.tableWidget.item(9, 3)
        ___qtablewidgetitem54.setText(QCoreApplication.translate("FusionGameTabWidget", u"Regular Hint, Featural", None));
        ___qtablewidgetitem55 = self.tableWidget.item(10, 0)
        ___qtablewidgetitem55.setText(QCoreApplication.translate("FusionGameTabWidget", u"Sector 6 (NOC)", None));
        ___qtablewidgetitem56 = self.tableWidget.item(10, 1)
        ___qtablewidgetitem56.setText(QCoreApplication.translate("FusionGameTabWidget", u"Entrance Navigation Room", None));
        ___qtablewidgetitem57 = self.tableWidget.item(10, 2)
        ___qtablewidgetitem57.setText(QCoreApplication.translate("FusionGameTabWidget", u"Level 4 Keycard (RED)", None));
        ___qtablewidgetitem58 = self.tableWidget.item(10, 3)
        ___qtablewidgetitem58.setText(QCoreApplication.translate("FusionGameTabWidget", u"Regular Hint, Featural", None));
        self.tableWidget.setSortingEnabled(__sortingEnabled)

        self.label.setText(QCoreApplication.translate("FusionGameTabWidget", u"<html><head/><body><p><br/></p></body></html>", None))
        FusionGameTabWidget.setTabText(FusionGameTabWidget.indexOf(self.hints_tab), QCoreApplication.translate("FusionGameTabWidget", u"Hints", None))
        FusionGameTabWidget.setTabText(FusionGameTabWidget.indexOf(self.pickup_hint_features_tab), QCoreApplication.translate("FusionGameTabWidget", u"Pickup Hint Features", None))
        FusionGameTabWidget.setTabText(FusionGameTabWidget.indexOf(self.location_hint_features_tab), QCoreApplication.translate("FusionGameTabWidget", u"Location Hint Features", None))
        pass
    # retranslateUi

