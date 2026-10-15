# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'games_tab_prime2_opr_widget.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QGridLayout, QHBoxLayout,
    QHeaderView, QLabel, QPushButton, QScrollArea,
    QSizePolicy, QSpacerItem, QTabWidget, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout, QWidget)

from randovania.gui.widgets.generate_game_widget import GenerateGameWidget
from randovania.gui.widgets.hint_feature_tab import (LocationHintFeatureTab, PickupHintFeatureTab)

class Ui_EchoesOPRGameTabWidget(object):
    def setupUi(self, EchoesOPRGameTabWidget):
        if not EchoesOPRGameTabWidget.objectName():
            EchoesOPRGameTabWidget.setObjectName(u"EchoesOPRGameTabWidget")
        EchoesOPRGameTabWidget.resize(501, 393)
        EchoesOPRGameTabWidget.setDocumentMode(True)
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

        EchoesOPRGameTabWidget.addTab(self.tab_intro, "")
        self.tab_generate_game = GenerateGameWidget()
        self.tab_generate_game.setObjectName(u"tab_generate_game")
        EchoesOPRGameTabWidget.addTab(self.tab_generate_game, "")
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

        EchoesOPRGameTabWidget.addTab(self.faq_tab, "")
        self.differences_tab = QWidget()
        self.differences_tab.setObjectName(u"differences_tab")
        self.verticalLayout_3 = QVBoxLayout(self.differences_tab)
        self.verticalLayout_3.setSpacing(6)
        self.verticalLayout_3.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.differences_scroll_area = QScrollArea(self.differences_tab)
        self.differences_scroll_area.setObjectName(u"differences_scroll_area")
        self.differences_scroll_area.setWidgetResizable(True)
        self.differences_scroll_contents = QWidget()
        self.differences_scroll_contents.setObjectName(u"differences_scroll_contents")
        self.differences_scroll_contents.setGeometry(QRect(0, 0, 481, 345))
        self.differences_scroll_layout_3 = QVBoxLayout(self.differences_scroll_contents)
        self.differences_scroll_layout_3.setSpacing(6)
        self.differences_scroll_layout_3.setContentsMargins(11, 11, 11, 11)
        self.differences_scroll_layout_3.setObjectName(u"differences_scroll_layout_3")
        self.differences_label = QLabel(self.differences_scroll_contents)
        self.differences_label.setObjectName(u"differences_label")
        self.differences_label.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        self.differences_label.setWordWrap(True)

        self.differences_scroll_layout_3.addWidget(self.differences_label)

        self.differences_scroll_area.setWidget(self.differences_scroll_contents)

        self.verticalLayout_3.addWidget(self.differences_scroll_area)

        EchoesOPRGameTabWidget.addTab(self.differences_tab, "")
        self.hints_tab = QWidget()
        self.hints_tab.setObjectName(u"hints_tab")
        self.verticalLayout_2 = QVBoxLayout(self.hints_tab)
        self.verticalLayout_2.setSpacing(6)
        self.verticalLayout_2.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.hints_scroll_area = QScrollArea(self.hints_tab)
        self.hints_scroll_area.setObjectName(u"hints_scroll_area")
        self.hints_scroll_area.setWidgetResizable(True)
        self.hints_scroll_area_contents = QWidget()
        self.hints_scroll_area_contents.setObjectName(u"hints_scroll_area_contents")
        self.hints_scroll_area_contents.setGeometry(QRect(0, 0, 467, 682))
        self.hints_scroll_layout = QVBoxLayout(self.hints_scroll_area_contents)
        self.hints_scroll_layout.setSpacing(6)
        self.hints_scroll_layout.setContentsMargins(11, 11, 11, 11)
        self.hints_scroll_layout.setObjectName(u"hints_scroll_layout")
        self.hints_label = QLabel(self.hints_scroll_area_contents)
        self.hints_label.setObjectName(u"hints_label")
        self.hints_label.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        self.hints_label.setWordWrap(True)

        self.hints_scroll_layout.addWidget(self.hints_label)

        self.hints_scroll_area.setWidget(self.hints_scroll_area_contents)

        self.verticalLayout_2.addWidget(self.hints_scroll_area)

        EchoesOPRGameTabWidget.addTab(self.hints_tab, "")
        self.pickup_hint_features_tab = PickupHintFeatureTab()
        self.pickup_hint_features_tab.setObjectName(u"pickup_hint_features_tab")
        EchoesOPRGameTabWidget.addTab(self.pickup_hint_features_tab, "")
        self.location_hint_features_tab = LocationHintFeatureTab()
        self.location_hint_features_tab.setObjectName(u"location_hint_features_tab")
        EchoesOPRGameTabWidget.addTab(self.location_hint_features_tab, "")
        self.hint_locations_tab = QWidget()
        self.hint_locations_tab.setObjectName(u"hint_locations_tab")
        self.verticalLayout = QVBoxLayout(self.hint_locations_tab)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.hint_locations_scroll_area = QScrollArea(self.hint_locations_tab)
        self.hint_locations_scroll_area.setObjectName(u"hint_locations_scroll_area")
        self.hint_locations_scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.hint_locations_scroll_area.setFrameShadow(QFrame.Shadow.Plain)
        self.hint_locations_scroll_area.setLineWidth(1)
        self.hint_locations_scroll_area.setWidgetResizable(True)
        self.hint_locations_scroll_area.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        self.hint_locations_scroll_contents = QWidget()
        self.hint_locations_scroll_contents.setObjectName(u"hint_locations_scroll_contents")
        self.hint_locations_scroll_contents.setGeometry(QRect(0, 0, 483, 347))
        self.hint_scroll_layout = QVBoxLayout(self.hint_locations_scroll_contents)
        self.hint_scroll_layout.setSpacing(6)
        self.hint_scroll_layout.setContentsMargins(11, 11, 11, 11)
        self.hint_scroll_layout.setObjectName(u"hint_scroll_layout")
        self.hint_locations_label = QLabel(self.hint_locations_scroll_contents)
        self.hint_locations_label.setObjectName(u"hint_locations_label")
        self.hint_locations_label.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        self.hint_locations_label.setWordWrap(True)

        self.hint_scroll_layout.addWidget(self.hint_locations_label)

        self.hint_locations_tree_widget = QTreeWidget(self.hint_locations_scroll_contents)
        self.hint_locations_tree_widget.setObjectName(u"hint_locations_tree_widget")

        self.hint_scroll_layout.addWidget(self.hint_locations_tree_widget)

        self.hint_locations_scroll_area.setWidget(self.hint_locations_scroll_contents)

        self.verticalLayout.addWidget(self.hint_locations_scroll_area)

        EchoesOPRGameTabWidget.addTab(self.hint_locations_tab, "")

        self.retranslateUi(EchoesOPRGameTabWidget)

        EchoesOPRGameTabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(EchoesOPRGameTabWidget)
    # setupUi

    def retranslateUi(self, EchoesOPRGameTabWidget):
        self.game_cover_label.setText(QCoreApplication.translate("EchoesOPRGameTabWidget", u"TextLabel", None))
        self.intro_label.setText(QCoreApplication.translate("EchoesOPRGameTabWidget", u"<html><head/><body><p>Navigate Aether and Dark Aether in search of the Sky Temple Keys, then defeat Emperor Ing and Dark Samus to win the war for the Luminoth!</p><p align=\"justify\">The totems in Sky Temple Gateway can be scanned to receive hints on the locations of each Sky Temple Key. Likewise, the gates for the three Dark Temples can be scanned to receive hints on the locations of each Dark Temple Key. </p><p align=\"justify\">Luminoth Lore can be scanned for general hints, and you can optionally enable scanning Keybearer Corpses to receive a vague hint about the item in their respective Flying Ing Cache.</p><p align=\"justify\">Don't forget to check out our <a href=\"tab://FAQ\">Frequently Asked Questions</a> and the list of <a href=\"tab://Differences\">Differences</a> from the vanilla game.</p><p align=\"justify\">To get started, use the Quick Generate button to generate a game using the default settings!</p></body></html>", None))
        self.quick_generate_button.setText(QCoreApplication.translate("EchoesOPRGameTabWidget", u"Quick generate", None))
        EchoesOPRGameTabWidget.setTabText(EchoesOPRGameTabWidget.indexOf(self.tab_intro), QCoreApplication.translate("EchoesOPRGameTabWidget", u"Introduction", None))
        EchoesOPRGameTabWidget.setTabText(EchoesOPRGameTabWidget.indexOf(self.tab_generate_game), QCoreApplication.translate("EchoesOPRGameTabWidget", u"Play", None))
        self.faq_label.setText(QCoreApplication.translate("EchoesOPRGameTabWidget", u"# updated from code", None))
        EchoesOPRGameTabWidget.setTabText(EchoesOPRGameTabWidget.indexOf(self.faq_tab), QCoreApplication.translate("EchoesOPRGameTabWidget", u"FAQ", None))
        self.differences_label.setText(QCoreApplication.translate("EchoesOPRGameTabWidget", u"<html><head/><body><p>Randovania makes some changes to the original game in order to improve the game experience or to simply fix bugs in the original game.</p><ul style=\"margin-top: 0px; margin-bottom: 0px; margin-left: 0px; margin-right: 0px; -qt-list-indent: 1;\"><li style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">TODO: Go over all of this based on the OPR changes</li></ul></body></html>", None))
        EchoesOPRGameTabWidget.setTabText(EchoesOPRGameTabWidget.indexOf(self.differences_tab), QCoreApplication.translate("EchoesOPRGameTabWidget", u"Differences", None))
        self.hints_label.setText(QCoreApplication.translate("EchoesOPRGameTabWidget", u"<html><head/><body><p align=\"justify\">In Metroid Prime 2: Echoes, a number of hints are available to assist with your routing. Note: <span style=\" font-weight:700;\">A pickup location can't receive more than one hint.</span></p><p align=\"justify\">You can find hints from the following sources:</p><p align=\"justify\"><span style=\" font-weight:700;\">Sky Temple Gateway</span>: Hints for where each of your 9 Sky Temple Keys are located. In a Multiworld, describes which player has the keys as well.</p><p align=\"justify\"><span style=\" font-weight:700;\">Keybearer Corpse</span>: Contains a hint for the Flying Ing Cache in the associated room for the corpse. This hint will use a low-precision Hint Feature to describe the pickup, as listed in the Pickup Hint Features tab.</p><p align=\"justify\"><span style=\" font-weight:700;\">Dark Temple Gates</span>: The regions where this temple's keys can be located, listed in alphabetical order. In multiworld, the region listed might be someone else's, but the hint is "
                        "referring to your keys.</p><p align=\"justify\"><span style=\" font-weight:700;\">Luminoth Lore</span>: Contains the guaranteed hints and pickup hints.</p><hr/><p align=\"justify\">In each game, each of the following guaranteed hints are placed on a Luminoth Lore scan, placed randomly - this means they can be locked behind what they hint for. The hints are:</p><p align=\"justify\"><span style=\" font-weight:700;\">Joke Hints</span>: A joke. Uses green text and is a waste of space. There are 2 joke hints per game.</p><hr/><p align=\"justify\">The remaining Luminoth Lores are filled with standard pickup hints. These hints are placed according to the following priority:</p><p align=\"justify\"><span style=\" font-weight:600;\">1)</span> Pickups that were placed by the generator, after the hint became accessible. This helps ensure that hints don't point towards the pickups required to read the hint in the first place. These hints are placed starting with the hint with the fewest logical candidates.</p><p align=\"j"
                        "ustify\"><span style=\" font-weight:600;\">2)</span> If there were no logical candidates for a hint, it can instead point to any major pickup.</p><p align=\"justify\"><span style=\" font-weight:600;\">3)</span> At this point, we're out of useful candidates to hint, so the hint will simply pick any random pickup location.</p><p align=\"justify\"><br/></p></body></html>", None))
        EchoesOPRGameTabWidget.setTabText(EchoesOPRGameTabWidget.indexOf(self.hints_tab), QCoreApplication.translate("EchoesOPRGameTabWidget", u"Hints", None))
        EchoesOPRGameTabWidget.setTabText(EchoesOPRGameTabWidget.indexOf(self.pickup_hint_features_tab), QCoreApplication.translate("EchoesOPRGameTabWidget", u"Pickup Hint Features", None))
        EchoesOPRGameTabWidget.setTabText(EchoesOPRGameTabWidget.indexOf(self.location_hint_features_tab), QCoreApplication.translate("EchoesOPRGameTabWidget", u"Location Hint Features", None))
        self.hint_locations_label.setText(QCoreApplication.translate("EchoesOPRGameTabWidget", u"<html><head/><body><p>Hints\n"
"                                                are placed in the game by replacing Logbook scans. The\n"
"                                                following are the scans that may have a hint added to\n"
"                                                them:</p></body></html>\n"
"                                            ", None))
        ___qtreewidgetitem = self.hint_locations_tree_widget.headerItem()
        ___qtreewidgetitem.setText(0, QCoreApplication.translate("EchoesOPRGameTabWidget", u"Location", None))
        EchoesOPRGameTabWidget.setTabText(EchoesOPRGameTabWidget.indexOf(self.hint_locations_tab), QCoreApplication.translate("EchoesOPRGameTabWidget", u"Hint Locations", None))
        pass
    # retranslateUi

