# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'games_tab_planets_zebeth_widget.ui'
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

class Ui_PlanetsZebethGameTabWidget(object):
    def setupUi(self, PlanetsZebethGameTabWidget):
        if not PlanetsZebethGameTabWidget.objectName():
            PlanetsZebethGameTabWidget.setObjectName(u"PlanetsZebethGameTabWidget")
        PlanetsZebethGameTabWidget.resize(574, 449)
        PlanetsZebethGameTabWidget.setDocumentMode(True)
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

        PlanetsZebethGameTabWidget.addTab(self.tab_intro, "")
        self.tab_generate_game = GenerateGameWidget()
        self.tab_generate_game.setObjectName(u"tab_generate_game")
        PlanetsZebethGameTabWidget.addTab(self.tab_generate_game, "")
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
        self.faq_scroll_area_contents.setGeometry(QRect(0, 0, 572, 419))
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

        PlanetsZebethGameTabWidget.addTab(self.faq_tab, "")
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
        self.differences_scroll_contents.setGeometry(QRect(0, 0, 540, 402))
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

        PlanetsZebethGameTabWidget.addTab(self.differences_tab, "")
        self.pickup_hint_features_tab = PickupHintFeatureTab()
        self.pickup_hint_features_tab.setObjectName(u"pickup_hint_features_tab")
        PlanetsZebethGameTabWidget.addTab(self.pickup_hint_features_tab, "")

        self.retranslateUi(PlanetsZebethGameTabWidget)

        PlanetsZebethGameTabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(PlanetsZebethGameTabWidget)
    # setupUi

    def retranslateUi(self, PlanetsZebethGameTabWidget):
        self.game_cover_label.setText(QCoreApplication.translate("PlanetsZebethGameTabWidget", u"TextLabel", None))
        self.intro_label.setText(QCoreApplication.translate("PlanetsZebethGameTabWidget", u"<html><head/><body>\n"
"<p>Traverse the depths of Zebes to gather the 9 Tourian Keys in order to fight Mother Brain and escape the planet.</p>\n"
"<p>Blocks will block the path to Tourian, until you get all 9 Tourian Keys. You can randomize them or find them in their vanilla location.</p>\n"
"<p>For more details, check out the <a href=\"tab://FAQ\"><span style=\" text-decoration: underline; color:#007af4;\">FAQ</span></a> and <a href=\"tab://Differences\"><span style=\" text-decoration: underline; color:#007af4;\">Differences</span></a> tabs.</p>\n"
"<p>To get started, use the Quick Generate button to generate a game using the default settings!</p></body></html>", None))
        self.quick_generate_button.setText(QCoreApplication.translate("PlanetsZebethGameTabWidget", u"Quick generate", None))
        PlanetsZebethGameTabWidget.setTabText(PlanetsZebethGameTabWidget.indexOf(self.tab_intro), QCoreApplication.translate("PlanetsZebethGameTabWidget", u"Introduction", None))
        PlanetsZebethGameTabWidget.setTabText(PlanetsZebethGameTabWidget.indexOf(self.tab_generate_game), QCoreApplication.translate("PlanetsZebethGameTabWidget", u"Play", None))
        self.faq_label.setText(QCoreApplication.translate("PlanetsZebethGameTabWidget", u"# updated from code", None))
        PlanetsZebethGameTabWidget.setTabText(PlanetsZebethGameTabWidget.indexOf(self.faq_tab), QCoreApplication.translate("PlanetsZebethGameTabWidget", u"FAQ", None))
        self.differences_label.setText(QCoreApplication.translate("PlanetsZebethGameTabWidget", u"<html><head/><body><p>Randovania makes some changes to the original game in order to improve the game experience or to simply fix bugs in the original game.<br/>Many changes are optional and can be disabled in the options Randovania provides, but the following are <span style=\" font-weight:600;\">always</span> there:</p><ul style=\"margin-top: 0px; margin-bottom: 0px; margin-left: 0px; margin-right: 0px; -qt-list-indent: 1;\"><li style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Only Zebeth planet is available since we are randomizing original Metroid.</li><li style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">\n"
"The game will now use a different save directory.</li><li style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Kraid and Ridley now spawn 2 items (Big Missile and Tourian Key) which can be random"
                        "ized.</li></ul><p><br/></p><p><br/></p><p><br/></p><p><br/></p><p><br/></p></body></html>", None))
        PlanetsZebethGameTabWidget.setTabText(PlanetsZebethGameTabWidget.indexOf(self.differences_tab), QCoreApplication.translate("PlanetsZebethGameTabWidget", u"Differences", None))
        PlanetsZebethGameTabWidget.setTabText(PlanetsZebethGameTabWidget.indexOf(self.pickup_hint_features_tab), QCoreApplication.translate("PlanetsZebethGameTabWidget", u"Pickup Hint Features", None))
        pass
    # retranslateUi

