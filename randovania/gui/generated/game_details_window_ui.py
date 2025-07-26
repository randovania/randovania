# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'game_details_window.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QGridLayout, QLabel,
    QLineEdit, QMainWindow, QMenuBar, QProgressBar,
    QPushButton, QSizePolicy, QStatusBar, QTabWidget,
    QToolButton, QVBoxLayout, QWidget)

class Ui_GameDetailsWindow(object):
    def setupUi(self, GameDetailsWindow):
        if not GameDetailsWindow.objectName():
            GameDetailsWindow.setObjectName(u"GameDetailsWindow")
        GameDetailsWindow.resize(624, 471)
        self.centralWidget = QWidget(GameDetailsWindow)
        self.centralWidget.setObjectName(u"centralWidget")
        self.centralWidget.setMaximumSize(QSize(16777215, 16777215))
        self.centralWidget.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.verticalLayout = QVBoxLayout(self.centralWidget)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.layout_info_tab = QTabWidget(self.centralWidget)
        self.layout_info_tab.setObjectName(u"layout_info_tab")
        self.details_tab = QWidget()
        self.details_tab.setObjectName(u"details_tab")
        self.details_tab_layout = QGridLayout(self.details_tab)
        self.details_tab_layout.setSpacing(6)
        self.details_tab_layout.setContentsMargins(11, 11, 11, 11)
        self.details_tab_layout.setObjectName(u"details_tab_layout")
        self.details_tab_layout.setContentsMargins(4, 8, 4, 0)
        self.progress_bar = QProgressBar(self.details_tab)
        self.progress_bar.setObjectName(u"progress_bar")
        self.progress_bar.setMinimumSize(QSize(150, 0))
        self.progress_bar.setMaximumSize(QSize(150, 16777215))
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setInvertedAppearance(False)

        self.details_tab_layout.addWidget(self.progress_bar, 4, 0, 1, 1)

        self.layout_description_right_label = QLabel(self.details_tab)
        self.layout_description_right_label.setObjectName(u"layout_description_right_label")
        self.layout_description_right_label.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        self.layout_description_right_label.setWordWrap(True)

        self.details_tab_layout.addWidget(self.layout_description_right_label, 3, 3, 1, 4)

        self.permalink_edit = QLineEdit(self.details_tab)
        self.permalink_edit.setObjectName(u"permalink_edit")
        self.permalink_edit.setReadOnly(True)

        self.details_tab_layout.addWidget(self.permalink_edit, 0, 1, 1, 3)

        self.progress_label = QLabel(self.details_tab)
        self.progress_label.setObjectName(u"progress_label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.progress_label.sizePolicy().hasHeightForWidth())
        self.progress_label.setSizePolicy(sizePolicy)
        font = QFont()
        font.setPointSize(7)
        self.progress_label.setFont(font)
        self.progress_label.setTextFormat(Qt.TextFormat.MarkdownText)
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.progress_label.setWordWrap(True)
        self.progress_label.setOpenExternalLinks(True)

        self.details_tab_layout.addWidget(self.progress_label, 4, 1, 1, 1)

        self.player_index_combo = QComboBox(self.details_tab)
        self.player_index_combo.setObjectName(u"player_index_combo")

        self.details_tab_layout.addWidget(self.player_index_combo, 2, 0, 1, 4)

        self.layout_title_label = QLabel(self.details_tab)
        self.layout_title_label.setObjectName(u"layout_title_label")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.layout_title_label.sizePolicy().hasHeightForWidth())
        self.layout_title_label.setSizePolicy(sizePolicy1)
        self.layout_title_label.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByMouse|Qt.TextInteractionFlag.TextSelectableByMouse)

        self.details_tab_layout.addWidget(self.layout_title_label, 1, 0, 1, 4)

        self.tool_button = QToolButton(self.details_tab)
        self.tool_button.setObjectName(u"tool_button")
        self.tool_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        self.details_tab_layout.addWidget(self.tool_button, 1, 6, 1, 1)

        self.customize_user_preferences_button = QPushButton(self.details_tab)
        self.customize_user_preferences_button.setObjectName(u"customize_user_preferences_button")

        self.details_tab_layout.addWidget(self.customize_user_preferences_button, 2, 4, 1, 2)

        self.stop_background_process_button = QPushButton(self.details_tab)
        self.stop_background_process_button.setObjectName(u"stop_background_process_button")
        self.stop_background_process_button.setEnabled(False)
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.stop_background_process_button.sizePolicy().hasHeightForWidth())
        self.stop_background_process_button.setSizePolicy(sizePolicy2)
        self.stop_background_process_button.setMaximumSize(QSize(75, 16777215))
        self.stop_background_process_button.setCheckable(False)
        self.stop_background_process_button.setFlat(False)

        self.details_tab_layout.addWidget(self.stop_background_process_button, 4, 6, 1, 1)

        self.layout_description_left_label = QLabel(self.details_tab)
        self.layout_description_left_label.setObjectName(u"layout_description_left_label")
        self.layout_description_left_label.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        self.layout_description_left_label.setWordWrap(True)

        self.details_tab_layout.addWidget(self.layout_description_left_label, 3, 0, 1, 3)

        self.export_log_button = QPushButton(self.details_tab)
        self.export_log_button.setObjectName(u"export_log_button")

        self.details_tab_layout.addWidget(self.export_log_button, 1, 5, 1, 1)

        self.export_iso_button = QPushButton(self.details_tab)
        self.export_iso_button.setObjectName(u"export_iso_button")

        self.details_tab_layout.addWidget(self.export_iso_button, 1, 4, 1, 1)

        self.permalink_label = QLabel(self.details_tab)
        self.permalink_label.setObjectName(u"permalink_label")

        self.details_tab_layout.addWidget(self.permalink_label, 0, 0, 1, 1)

        self.layout_info_tab.addTab(self.details_tab, "")

        self.verticalLayout.addWidget(self.layout_info_tab)

        GameDetailsWindow.setCentralWidget(self.centralWidget)
        self.status_bar = QStatusBar(GameDetailsWindow)
        self.status_bar.setObjectName(u"status_bar")
        GameDetailsWindow.setStatusBar(self.status_bar)
        self.menuBar = QMenuBar(GameDetailsWindow)
        self.menuBar.setObjectName(u"menuBar")
        self.menuBar.setGeometry(QRect(0, 0, 624, 17))
        GameDetailsWindow.setMenuBar(self.menuBar)

        self.retranslateUi(GameDetailsWindow)

        self.layout_info_tab.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(GameDetailsWindow)
    # setupUi

    def retranslateUi(self, GameDetailsWindow):
        GameDetailsWindow.setWindowTitle(QCoreApplication.translate("GameDetailsWindow", u"Game Details", None))
        self.layout_description_right_label.setText(QCoreApplication.translate("GameDetailsWindow", u"<html><head/><body><p>This content should have been replaced by code.</p></body></html>", None))
        self.permalink_edit.setText(QCoreApplication.translate("GameDetailsWindow", u"<insert permalink here>", None))
        self.progress_label.setText("")
        self.layout_title_label.setText(QCoreApplication.translate("GameDetailsWindow", u"<html><head/><body><p>Seed Hash: ????<br/>Preset Name: ???</p></body></html>", None))
        self.tool_button.setText(QCoreApplication.translate("GameDetailsWindow", u"...", None))
        self.customize_user_preferences_button.setText(QCoreApplication.translate("GameDetailsWindow", u"Customize cosmetic options", None))
        self.stop_background_process_button.setText(QCoreApplication.translate("GameDetailsWindow", u"Stop", None))
        self.layout_description_left_label.setText(QCoreApplication.translate("GameDetailsWindow", u"<html><head/><body><p>This content should have been replaced by code.</p></body></html>", None))
        self.export_log_button.setText(QCoreApplication.translate("GameDetailsWindow", u"Save Spoiler", None))
        self.export_iso_button.setText(QCoreApplication.translate("GameDetailsWindow", u"Export Game", None))
        self.permalink_label.setText(QCoreApplication.translate("GameDetailsWindow", u"Permalink:", None))
        self.layout_info_tab.setTabText(self.layout_info_tab.indexOf(self.details_tab), QCoreApplication.translate("GameDetailsWindow", u"Summary", None))
    # retranslateUi

