# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'games_tab_fusion_widget.ui'
##
## Created by: Qt User Interface Compiler version 6.6.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import *  # type: ignore
from PySide6.QtGui import *  # type: ignore
from PySide6.QtWidgets import *  # type: ignore

from randovania.gui.widgets.generate_game_widget import *  # type: ignore

class Ui_FusionGameTabWidget(object):
    def setupUi(self, FusionGameTabWidget):
        if not FusionGameTabWidget.objectName():
            FusionGameTabWidget.setObjectName(u"FusionGameTabWidget")
        FusionGameTabWidget.resize(501, 393)
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
        self.faq_scroll_area_contents.setGeometry(QRect(0, 0, 495, 361))
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
        self.differences_scroll_contents.setGeometry(QRect(0, 0, 463, 446))
        self.verticalLayout = QVBoxLayout(self.differences_scroll_contents)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.differences_label = QLabel(self.differences_scroll_contents)
        self.differences_label.setObjectName(u"differences_label")
        self.differences_label.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)
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
        self.hints_scroll_area_contents.setGeometry(QRect(0, 0, 675, 565))
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
        if (self.tableWidget.columnCount() < 3):
            self.tableWidget.setColumnCount(3)
        font = QFont()
        font.setBold(True)
        __qtablewidgetitem = QTableWidgetItem()
        __qtablewidgetitem.setFont(font);
        self.tableWidget.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        __qtablewidgetitem1.setFont(font);
        self.tableWidget.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        __qtablewidgetitem2.setFont(font);
        self.tableWidget.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        if (self.tableWidget.rowCount() < 11):
            self.tableWidget.setRowCount(11)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.tableWidget.setVerticalHeaderItem(0, __qtablewidgetitem3)
        __qtablewidgetitem4 = QTableWidgetItem()
        self.tableWidget.setVerticalHeaderItem(1, __qtablewidgetitem4)
        __qtablewidgetitem5 = QTableWidgetItem()
        self.tableWidget.setVerticalHeaderItem(2, __qtablewidgetitem5)
        __qtablewidgetitem6 = QTableWidgetItem()
        self.tableWidget.setVerticalHeaderItem(3, __qtablewidgetitem6)
        __qtablewidgetitem7 = QTableWidgetItem()
        self.tableWidget.setVerticalHeaderItem(4, __qtablewidgetitem7)
        __qtablewidgetitem8 = QTableWidgetItem()
        self.tableWidget.setVerticalHeaderItem(5, __qtablewidgetitem8)
        __qtablewidgetitem9 = QTableWidgetItem()
        self.tableWidget.setVerticalHeaderItem(6, __qtablewidgetitem9)
        __qtablewidgetitem10 = QTableWidgetItem()
        self.tableWidget.setVerticalHeaderItem(7, __qtablewidgetitem10)
        __qtablewidgetitem11 = QTableWidgetItem()
        self.tableWidget.setVerticalHeaderItem(8, __qtablewidgetitem11)
        __qtablewidgetitem12 = QTableWidgetItem()
        self.tableWidget.setVerticalHeaderItem(9, __qtablewidgetitem12)
        __qtablewidgetitem13 = QTableWidgetItem()
        self.tableWidget.setVerticalHeaderItem(10, __qtablewidgetitem13)
        __qtablewidgetitem14 = QTableWidgetItem()
        self.tableWidget.setItem(0, 0, __qtablewidgetitem14)
        __qtablewidgetitem15 = QTableWidgetItem()
        self.tableWidget.setItem(0, 1, __qtablewidgetitem15)
        __qtablewidgetitem16 = QTableWidgetItem()
        self.tableWidget.setItem(0, 2, __qtablewidgetitem16)
        __qtablewidgetitem17 = QTableWidgetItem()
        self.tableWidget.setItem(1, 0, __qtablewidgetitem17)
        __qtablewidgetitem18 = QTableWidgetItem()
        self.tableWidget.setItem(1, 1, __qtablewidgetitem18)
        __qtablewidgetitem19 = QTableWidgetItem()
        self.tableWidget.setItem(1, 2, __qtablewidgetitem19)
        __qtablewidgetitem20 = QTableWidgetItem()
        self.tableWidget.setItem(2, 0, __qtablewidgetitem20)
        __qtablewidgetitem21 = QTableWidgetItem()
        self.tableWidget.setItem(2, 1, __qtablewidgetitem21)
        __qtablewidgetitem22 = QTableWidgetItem()
        self.tableWidget.setItem(2, 2, __qtablewidgetitem22)
        __qtablewidgetitem23 = QTableWidgetItem()
        self.tableWidget.setItem(3, 0, __qtablewidgetitem23)
        __qtablewidgetitem24 = QTableWidgetItem()
        self.tableWidget.setItem(3, 1, __qtablewidgetitem24)
        __qtablewidgetitem25 = QTableWidgetItem()
        self.tableWidget.setItem(3, 2, __qtablewidgetitem25)
        __qtablewidgetitem26 = QTableWidgetItem()
        self.tableWidget.setItem(4, 0, __qtablewidgetitem26)
        __qtablewidgetitem27 = QTableWidgetItem()
        self.tableWidget.setItem(4, 1, __qtablewidgetitem27)
        __qtablewidgetitem28 = QTableWidgetItem()
        self.tableWidget.setItem(4, 2, __qtablewidgetitem28)
        __qtablewidgetitem29 = QTableWidgetItem()
        self.tableWidget.setItem(5, 0, __qtablewidgetitem29)
        __qtablewidgetitem30 = QTableWidgetItem()
        self.tableWidget.setItem(5, 1, __qtablewidgetitem30)
        __qtablewidgetitem31 = QTableWidgetItem()
        self.tableWidget.setItem(5, 2, __qtablewidgetitem31)
        __qtablewidgetitem32 = QTableWidgetItem()
        self.tableWidget.setItem(6, 0, __qtablewidgetitem32)
        __qtablewidgetitem33 = QTableWidgetItem()
        self.tableWidget.setItem(6, 1, __qtablewidgetitem33)
        __qtablewidgetitem34 = QTableWidgetItem()
        self.tableWidget.setItem(6, 2, __qtablewidgetitem34)
        __qtablewidgetitem35 = QTableWidgetItem()
        self.tableWidget.setItem(7, 0, __qtablewidgetitem35)
        __qtablewidgetitem36 = QTableWidgetItem()
        self.tableWidget.setItem(7, 1, __qtablewidgetitem36)
        __qtablewidgetitem37 = QTableWidgetItem()
        self.tableWidget.setItem(7, 2, __qtablewidgetitem37)
        __qtablewidgetitem38 = QTableWidgetItem()
        self.tableWidget.setItem(8, 0, __qtablewidgetitem38)
        __qtablewidgetitem39 = QTableWidgetItem()
        self.tableWidget.setItem(8, 1, __qtablewidgetitem39)
        __qtablewidgetitem40 = QTableWidgetItem()
        self.tableWidget.setItem(8, 2, __qtablewidgetitem40)
        __qtablewidgetitem41 = QTableWidgetItem()
        self.tableWidget.setItem(9, 0, __qtablewidgetitem41)
        __qtablewidgetitem42 = QTableWidgetItem()
        self.tableWidget.setItem(9, 1, __qtablewidgetitem42)
        __qtablewidgetitem43 = QTableWidgetItem()
        self.tableWidget.setItem(9, 2, __qtablewidgetitem43)
        __qtablewidgetitem44 = QTableWidgetItem()
        self.tableWidget.setItem(10, 0, __qtablewidgetitem44)
        __qtablewidgetitem45 = QTableWidgetItem()
        self.tableWidget.setItem(10, 1, __qtablewidgetitem45)
        __qtablewidgetitem46 = QTableWidgetItem()
        self.tableWidget.setItem(10, 2, __qtablewidgetitem46)
        self.tableWidget.setObjectName(u"tableWidget")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.tableWidget.sizePolicy().hasHeightForWidth())
        self.tableWidget.setSizePolicy(sizePolicy1)
        self.tableWidget.setMinimumSize(QSize(660, 0))
        self.tableWidget.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContentsOnFirstShow)
        self.tableWidget.setAutoScroll(True)
        self.tableWidget.setRowCount(11)
        self.tableWidget.setColumnCount(3)
        self.tableWidget.horizontalHeader().setVisible(True)
        self.tableWidget.horizontalHeader().setCascadingSectionResizes(False)
        self.tableWidget.horizontalHeader().setMinimumSectionSize(30)
        self.tableWidget.horizontalHeader().setDefaultSectionSize(220)
        self.tableWidget.verticalHeader().setVisible(False)
        self.tableWidget.verticalHeader().setDefaultSectionSize(30)

        self.hints_scroll_layout_4.addWidget(self.tableWidget)

        self.line = QFrame(self.hints_scroll_area_contents)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

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
        self.hint_item_names_tab = QWidget()
        self.hint_item_names_tab.setObjectName(u"hint_item_names_tab")
        self.hint_item_names_layout_4 = QVBoxLayout(self.hint_item_names_tab)
        self.hint_item_names_layout_4.setSpacing(0)
        self.hint_item_names_layout_4.setContentsMargins(11, 11, 11, 11)
        self.hint_item_names_layout_4.setObjectName(u"hint_item_names_layout_4")
        self.hint_item_names_layout_4.setContentsMargins(0, 0, 0, 0)
        self.hint_item_names_scroll_area = QScrollArea(self.hint_item_names_tab)
        self.hint_item_names_scroll_area.setObjectName(u"hint_item_names_scroll_area")
        self.hint_item_names_scroll_area.setWidgetResizable(True)
        self.hint_item_names_scroll_area.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.hint_item_names_scroll_contents = QWidget()
        self.hint_item_names_scroll_contents.setObjectName(u"hint_item_names_scroll_contents")
        self.hint_item_names_scroll_contents.setGeometry(QRect(0, 0, 495, 361))
        self.hint_item_names_scroll_layout_4 = QVBoxLayout(self.hint_item_names_scroll_contents)
        self.hint_item_names_scroll_layout_4.setSpacing(6)
        self.hint_item_names_scroll_layout_4.setContentsMargins(11, 11, 11, 11)
        self.hint_item_names_scroll_layout_4.setObjectName(u"hint_item_names_scroll_layout_4")
        self.hint_item_names_label = QLabel(self.hint_item_names_scroll_contents)
        self.hint_item_names_label.setObjectName(u"hint_item_names_label")
        self.hint_item_names_label.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.hint_item_names_label.setWordWrap(True)

        self.hint_item_names_scroll_layout_4.addWidget(self.hint_item_names_label)

        self.hint_item_names_tree_widget = QTableWidget(self.hint_item_names_scroll_contents)
        if (self.hint_item_names_tree_widget.columnCount() < 4):
            self.hint_item_names_tree_widget.setColumnCount(4)
        __qtablewidgetitem47 = QTableWidgetItem()
        self.hint_item_names_tree_widget.setHorizontalHeaderItem(0, __qtablewidgetitem47)
        __qtablewidgetitem48 = QTableWidgetItem()
        self.hint_item_names_tree_widget.setHorizontalHeaderItem(1, __qtablewidgetitem48)
        __qtablewidgetitem49 = QTableWidgetItem()
        self.hint_item_names_tree_widget.setHorizontalHeaderItem(2, __qtablewidgetitem49)
        __qtablewidgetitem50 = QTableWidgetItem()
        self.hint_item_names_tree_widget.setHorizontalHeaderItem(3, __qtablewidgetitem50)
        self.hint_item_names_tree_widget.setObjectName(u"hint_item_names_tree_widget")
        self.hint_item_names_tree_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.hint_item_names_tree_widget.setSortingEnabled(True)

        self.hint_item_names_scroll_layout_4.addWidget(self.hint_item_names_tree_widget)

        self.hint_item_names_scroll_area.setWidget(self.hint_item_names_scroll_contents)

        self.hint_item_names_layout_4.addWidget(self.hint_item_names_scroll_area)

        FusionGameTabWidget.addTab(self.hint_item_names_tab, "")

        self.retranslateUi(FusionGameTabWidget)

        FusionGameTabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(FusionGameTabWidget)
    # setupUi

    def retranslateUi(self, FusionGameTabWidget):
        self.game_cover_label.setText(QCoreApplication.translate("FusionGameTabWidget", u"TextLabel", None))
        self.intro_label.setText(QCoreApplication.translate("FusionGameTabWidget", u"<html><head/><body><p align=\"justify\">Explore the B.S.L Station, collect the escaped Infant Metroids, all while gearing up to fight the SA-X before destroying the station.</p><p align=\"justify\">The Operations Controls will only be unlocked once all the Metroids are collected.</p><p align=\"justify\">To aid Samus on her journey, ADAM now provides hints at Navigation Stations, this is explained further on the <a href=\"tab://Hints\"><span style=\" text-decoration: underline; color:#007af4;\">Hints</span></a> Tabs.</p><p align=\"justify\">For more details, checkout the <a href=\"tab://FAQ\"><span style=\" text-decoration: underline; color:#007af4;\">FAQ</span></a> and <a href=\"tab://Differences\"><span style=\" text-decoration: underline; color:#007af4;\">Differences</span></a> tabs.</p><p align=\"justify\">To get started, use the Quick Generate button to generate a game using the default settings.</p></body></html>", None))
        self.quick_generate_button.setText(QCoreApplication.translate("FusionGameTabWidget", u"Quick generate", None))
        FusionGameTabWidget.setTabText(FusionGameTabWidget.indexOf(self.tab_intro), QCoreApplication.translate("FusionGameTabWidget", u"Introduction", None))
        FusionGameTabWidget.setTabText(FusionGameTabWidget.indexOf(self.tab_generate_game), QCoreApplication.translate("FusionGameTabWidget", u"Play", None))
        self.faq_label.setText(QCoreApplication.translate("FusionGameTabWidget", u"# updated from code", None))
        FusionGameTabWidget.setTabText(FusionGameTabWidget.indexOf(self.faq_tab), QCoreApplication.translate("FusionGameTabWidget", u"FAQ", None))
        self.differences_label.setText(QCoreApplication.translate("FusionGameTabWidget", u"<html><head/><body><p>Randovania and the MARS patcher make some changes to the original game in order to improve the game experience or to simply fix bugs in the original game.<br/>Many changes are optional and can be disabled in the options Randovania provides, but the following are <span style=\" font-weight:600;\">always</span> there:</p><ul style=\"margin-top: 0px; margin-bottom: 0px; margin-left: 0px; margin-right: 0px; -qt-list-indent: 1;\"><li style=\" margin-top:12px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">An option has been added to the pause menu that allows loading your last save from your starting location.</li><li style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">An option has been added to cycle the Sectors on the map by pressing SELECT.</li></ul><ul style=\"margin-top: 0px; margin-bottom: 0px; margin-left: 0px; margin-right: 0px; -qt-list-indent: 1;\"><li style=\" margin-to"
                        "p:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">The Security Rooms are now item locations and the locks can be shuffled into the item pool.</li><li style=\" margin-top:12px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Hints have been placed at Navigation Stations.</li><li style=\" margin-top:12px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Main Deck Maintenance Shaft now has a connection between Crew Quarters East/West</li><ul style=\"margin-top: 0px; margin-bottom: 0px; margin-left: 0px; margin-right: 0px; -qt-list-indent: 1;\"><li style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Sector 5 will always remain in it's unbroken state, some rooms have been modified to account for this.</li></ul><li style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent"
                        ":0; text-indent:0px;\">The upper right door in S5 Arctic Containment is now a Yellow Door.</li><li style=\" margin-top:12px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Sector 6 Varia Core-X always spawns regardless of having Charge Beam or not.</li></ul><p><br/></p></body></html>", None))
        FusionGameTabWidget.setTabText(FusionGameTabWidget.indexOf(self.differences_tab), QCoreApplication.translate("FusionGameTabWidget", u"Differences", None))
        self.hints_label.setText(QCoreApplication.translate("FusionGameTabWidget", u"<html><head/><body><p>In Metroid Fusion, you can find hints for the following resources: </p><p><span style=\" font-weight:700;\">Metroids</span>: The Restricted Area Navigation Room hints where all your Infant Metroids are.</p><p><span style=\" font-weight:700;\">Major Items</span>: All other Navigation Rooms provide a hint to a major item with varying degress of precision as described below:</p></body></html>", None))
        ___qtablewidgetitem = self.tableWidget.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("FusionGameTabWidget", u"Region", None));
        ___qtablewidgetitem1 = self.tableWidget.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("FusionGameTabWidget", u"Area", None));
        ___qtablewidgetitem2 = self.tableWidget.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("FusionGameTabWidget", u"Hint Precision", None));
        ___qtablewidgetitem3 = self.tableWidget.verticalHeaderItem(0)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("FusionGameTabWidget", u"New Row", None));
        ___qtablewidgetitem4 = self.tableWidget.verticalHeaderItem(1)
        ___qtablewidgetitem4.setText(QCoreApplication.translate("FusionGameTabWidget", u"New Row", None));
        ___qtablewidgetitem5 = self.tableWidget.verticalHeaderItem(2)
        ___qtablewidgetitem5.setText(QCoreApplication.translate("FusionGameTabWidget", u"New Row", None));
        ___qtablewidgetitem6 = self.tableWidget.verticalHeaderItem(3)
        ___qtablewidgetitem6.setText(QCoreApplication.translate("FusionGameTabWidget", u"New Row", None));
        ___qtablewidgetitem7 = self.tableWidget.verticalHeaderItem(4)
        ___qtablewidgetitem7.setText(QCoreApplication.translate("FusionGameTabWidget", u"New Row", None));
        ___qtablewidgetitem8 = self.tableWidget.verticalHeaderItem(5)
        ___qtablewidgetitem8.setText(QCoreApplication.translate("FusionGameTabWidget", u"New Row", None));
        ___qtablewidgetitem9 = self.tableWidget.verticalHeaderItem(6)
        ___qtablewidgetitem9.setText(QCoreApplication.translate("FusionGameTabWidget", u"New Row", None));
        ___qtablewidgetitem10 = self.tableWidget.verticalHeaderItem(7)
        ___qtablewidgetitem10.setText(QCoreApplication.translate("FusionGameTabWidget", u"New Row", None));
        ___qtablewidgetitem11 = self.tableWidget.verticalHeaderItem(8)
        ___qtablewidgetitem11.setText(QCoreApplication.translate("FusionGameTabWidget", u"New Row", None));
        ___qtablewidgetitem12 = self.tableWidget.verticalHeaderItem(9)
        ___qtablewidgetitem12.setText(QCoreApplication.translate("FusionGameTabWidget", u"New Row", None));
        ___qtablewidgetitem13 = self.tableWidget.verticalHeaderItem(10)
        ___qtablewidgetitem13.setText(QCoreApplication.translate("FusionGameTabWidget", u"New Row", None));

        __sortingEnabled = self.tableWidget.isSortingEnabled()
        self.tableWidget.setSortingEnabled(False)
        ___qtablewidgetitem14 = self.tableWidget.item(0, 0)
        ___qtablewidgetitem14.setText(QCoreApplication.translate("FusionGameTabWidget", u"Main Deck", None));
        ___qtablewidgetitem15 = self.tableWidget.item(0, 1)
        ___qtablewidgetitem15.setText(QCoreApplication.translate("FusionGameTabWidget", u"Auxiliary Navigation Room", None));
        ___qtablewidgetitem16 = self.tableWidget.item(0, 2)
        ___qtablewidgetitem16.setText(QCoreApplication.translate("FusionGameTabWidget", u"Charge Beam, Configurable Precision", None));
        ___qtablewidgetitem17 = self.tableWidget.item(1, 0)
        ___qtablewidgetitem17.setText(QCoreApplication.translate("FusionGameTabWidget", u"Main Deck", None));
        ___qtablewidgetitem18 = self.tableWidget.item(1, 1)
        ___qtablewidgetitem18.setText(QCoreApplication.translate("FusionGameTabWidget", u"Main Deck Navigation Room East", None));
        ___qtablewidgetitem19 = self.tableWidget.item(1, 2)
        ___qtablewidgetitem19.setText(QCoreApplication.translate("FusionGameTabWidget", u"Broad Item, Broad Location", None));
        ___qtablewidgetitem20 = self.tableWidget.item(2, 0)
        ___qtablewidgetitem20.setText(QCoreApplication.translate("FusionGameTabWidget", u"Main Deck", None));
        ___qtablewidgetitem21 = self.tableWidget.item(2, 1)
        ___qtablewidgetitem21.setText(QCoreApplication.translate("FusionGameTabWidget", u"Main Deck Navigation Room West", None));
        ___qtablewidgetitem22 = self.tableWidget.item(2, 2)
        ___qtablewidgetitem22.setText(QCoreApplication.translate("FusionGameTabWidget", u"Broad Item, Broad Location", None));
        ___qtablewidgetitem23 = self.tableWidget.item(3, 0)
        ___qtablewidgetitem23.setText(QCoreApplication.translate("FusionGameTabWidget", u"Main Deck", None));
        ___qtablewidgetitem24 = self.tableWidget.item(3, 1)
        ___qtablewidgetitem24.setText(QCoreApplication.translate("FusionGameTabWidget", u"Operations Deck Navigation Room", None));
        ___qtablewidgetitem25 = self.tableWidget.item(3, 2)
        ___qtablewidgetitem25.setText(QCoreApplication.translate("FusionGameTabWidget", u"Broad Item, Broad Location", None));
        ___qtablewidgetitem26 = self.tableWidget.item(4, 0)
        ___qtablewidgetitem26.setText(QCoreApplication.translate("FusionGameTabWidget", u"Main Deck", None));
        ___qtablewidgetitem27 = self.tableWidget.item(4, 1)
        ___qtablewidgetitem27.setText(QCoreApplication.translate("FusionGameTabWidget", u"Restricted Navigation Room", None));
        ___qtablewidgetitem28 = self.tableWidget.item(4, 2)
        ___qtablewidgetitem28.setText(QCoreApplication.translate("FusionGameTabWidget", u"Infant Metroids, Configurable Precision", None));
        ___qtablewidgetitem29 = self.tableWidget.item(5, 0)
        ___qtablewidgetitem29.setText(QCoreApplication.translate("FusionGameTabWidget", u"Sector 1 (SRX)", None));
        ___qtablewidgetitem30 = self.tableWidget.item(5, 1)
        ___qtablewidgetitem30.setText(QCoreApplication.translate("FusionGameTabWidget", u"Entrance Navigation Room", None));
        ___qtablewidgetitem31 = self.tableWidget.item(5, 2)
        ___qtablewidgetitem31.setText(QCoreApplication.translate("FusionGameTabWidget", u"Broad Item, Broad Location", None));
        ___qtablewidgetitem32 = self.tableWidget.item(6, 0)
        ___qtablewidgetitem32.setText(QCoreApplication.translate("FusionGameTabWidget", u"Sector 2 (TRO)", None));
        ___qtablewidgetitem33 = self.tableWidget.item(6, 1)
        ___qtablewidgetitem33.setText(QCoreApplication.translate("FusionGameTabWidget", u"Entrance Navigation Room", None));
        ___qtablewidgetitem34 = self.tableWidget.item(6, 2)
        ___qtablewidgetitem34.setText(QCoreApplication.translate("FusionGameTabWidget", u"Broad Item, Broad Location", None));
        ___qtablewidgetitem35 = self.tableWidget.item(7, 0)
        ___qtablewidgetitem35.setText(QCoreApplication.translate("FusionGameTabWidget", u"Sector 3 (PYR)", None));
        ___qtablewidgetitem36 = self.tableWidget.item(7, 1)
        ___qtablewidgetitem36.setText(QCoreApplication.translate("FusionGameTabWidget", u"Entrance Navigation Room", None));
        ___qtablewidgetitem37 = self.tableWidget.item(7, 2)
        ___qtablewidgetitem37.setText(QCoreApplication.translate("FusionGameTabWidget", u"Broad Item, Broad Location", None));
        ___qtablewidgetitem38 = self.tableWidget.item(8, 0)
        ___qtablewidgetitem38.setText(QCoreApplication.translate("FusionGameTabWidget", u"Sector 4 (AQA)", None));
        ___qtablewidgetitem39 = self.tableWidget.item(8, 1)
        ___qtablewidgetitem39.setText(QCoreApplication.translate("FusionGameTabWidget", u"Entrance Navigation Room", None));
        ___qtablewidgetitem40 = self.tableWidget.item(8, 2)
        ___qtablewidgetitem40.setText(QCoreApplication.translate("FusionGameTabWidget", u"Broad Item, Broad Location", None));
        ___qtablewidgetitem41 = self.tableWidget.item(9, 0)
        ___qtablewidgetitem41.setText(QCoreApplication.translate("FusionGameTabWidget", u"Sector 5 (ARC)", None));
        ___qtablewidgetitem42 = self.tableWidget.item(9, 1)
        ___qtablewidgetitem42.setText(QCoreApplication.translate("FusionGameTabWidget", u"Entrance Navigation Room", None));
        ___qtablewidgetitem43 = self.tableWidget.item(9, 2)
        ___qtablewidgetitem43.setText(QCoreApplication.translate("FusionGameTabWidget", u"Broad Item, Broad Location", None));
        ___qtablewidgetitem44 = self.tableWidget.item(10, 0)
        ___qtablewidgetitem44.setText(QCoreApplication.translate("FusionGameTabWidget", u"Sector 6 (NOC)", None));
        ___qtablewidgetitem45 = self.tableWidget.item(10, 1)
        ___qtablewidgetitem45.setText(QCoreApplication.translate("FusionGameTabWidget", u"Entrance Navigation Room", None));
        ___qtablewidgetitem46 = self.tableWidget.item(10, 2)
        ___qtablewidgetitem46.setText(QCoreApplication.translate("FusionGameTabWidget", u"Broad Item, Broad Location", None));
        self.tableWidget.setSortingEnabled(__sortingEnabled)

        self.label.setText(QCoreApplication.translate("FusionGameTabWidget", u"<html><head/><body><p><br/></p></body></html>", None))
        FusionGameTabWidget.setTabText(FusionGameTabWidget.indexOf(self.hints_tab), QCoreApplication.translate("FusionGameTabWidget", u"Hints", None))
        self.hint_item_names_label.setText(QCoreApplication.translate("FusionGameTabWidget", u"<html><head/><body><p>When\n"
"                                                items are referenced in a hint, multiple names can be\n"
"                                                used depending on how precise the hint is. The names\n"
"                                                each item can use are the following:</p></body></html>\n"
"                                            ", None))
        ___qtablewidgetitem47 = self.hint_item_names_tree_widget.horizontalHeaderItem(0)
        ___qtablewidgetitem47.setText(QCoreApplication.translate("FusionGameTabWidget", u"Item", None));
        ___qtablewidgetitem48 = self.hint_item_names_tree_widget.horizontalHeaderItem(1)
        ___qtablewidgetitem48.setText(QCoreApplication.translate("FusionGameTabWidget", u"Precise Category", None));
        ___qtablewidgetitem49 = self.hint_item_names_tree_widget.horizontalHeaderItem(2)
        ___qtablewidgetitem49.setText(QCoreApplication.translate("FusionGameTabWidget", u"General Category", None));
        ___qtablewidgetitem50 = self.hint_item_names_tree_widget.horizontalHeaderItem(3)
        ___qtablewidgetitem50.setText(QCoreApplication.translate("FusionGameTabWidget", u"Broad Category", None));
        FusionGameTabWidget.setTabText(FusionGameTabWidget.indexOf(self.hint_item_names_tab), QCoreApplication.translate("FusionGameTabWidget", u"Hint Item Names", None))
        pass
    # retranslateUi

