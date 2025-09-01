# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_window.ui'
##
## Created by: Qt User Interface Compiler version 6.9.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QFrame, QGridLayout, QLabel,
    QMainWindow, QMenu, QMenuBar, QProgressBar,
    QPushButton, QScrollArea, QSizePolicy, QSpacerItem,
    QStatusBar, QTabWidget, QVBoxLayout, QWidget)

from randovania.gui.widgets.games_help_widget import GamesHelpWidget

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(688, 582)
        MainWindow.setMaximumSize(QSize(16777215, 16777215))
        self.menu_action_edit_existing_database = QAction(MainWindow)
        self.menu_action_edit_existing_database.setObjectName(u"menu_action_edit_existing_database")
        self.menu_action_validate_seed_after = QAction(MainWindow)
        self.menu_action_validate_seed_after.setObjectName(u"menu_action_validate_seed_after")
        self.menu_action_validate_seed_after.setCheckable(True)
        self.menu_action_validate_seed_after.setChecked(True)
        self.menu_action_timeout_generation_after_a_time_limit = QAction(MainWindow)
        self.menu_action_timeout_generation_after_a_time_limit.setObjectName(u"menu_action_timeout_generation_after_a_time_limit")
        self.menu_action_timeout_generation_after_a_time_limit.setCheckable(True)
        self.menu_action_timeout_generation_after_a_time_limit.setChecked(True)
        self.menu_action_open_auto_tracker = QAction(MainWindow)
        self.menu_action_open_auto_tracker.setObjectName(u"menu_action_open_auto_tracker")
        self.menu_action_login_window = QAction(MainWindow)
        self.menu_action_login_window.setObjectName(u"menu_action_login_window")
        self.menu_action_dark_mode = QAction(MainWindow)
        self.menu_action_dark_mode.setObjectName(u"menu_action_dark_mode")
        self.menu_action_dark_mode.setCheckable(True)
        self.menu_action_show_multiworld_banner = QAction(MainWindow)
        self.menu_action_show_multiworld_banner.setObjectName(u"menu_action_show_multiworld_banner")
        self.menu_action_show_multiworld_banner.setCheckable(True)
        self.menu_action_previously_generated_games = QAction(MainWindow)
        self.menu_action_previously_generated_games.setObjectName(u"menu_action_previously_generated_games")
        self.menu_action_log_files_directory = QAction(MainWindow)
        self.menu_action_log_files_directory.setObjectName(u"menu_action_log_files_directory")
        self.menu_action_help = QAction(MainWindow)
        self.menu_action_help.setObjectName(u"menu_action_help")
        self.menu_action_changelog = QAction(MainWindow)
        self.menu_action_changelog.setObjectName(u"menu_action_changelog")
        self.menu_action_about = QAction(MainWindow)
        self.menu_action_about.setObjectName(u"menu_action_about")
        self.menu_action_dependencies = QAction(MainWindow)
        self.menu_action_dependencies.setObjectName(u"menu_action_dependencies")
        self.menu_action_experimental_settings = QAction(MainWindow)
        self.menu_action_experimental_settings.setObjectName(u"menu_action_experimental_settings")
        self.menu_action_experimental_settings.setCheckable(True)
        self.menu_action_automatic_reporting = QAction(MainWindow)
        self.menu_action_automatic_reporting.setObjectName(u"menu_action_automatic_reporting")
        self.menu_action_generate_in_another_process = QAction(MainWindow)
        self.menu_action_generate_in_another_process.setObjectName(u"menu_action_generate_in_another_process")
        self.menu_action_generate_in_another_process.setCheckable(True)
        self.menu_action_generate_in_another_process.setChecked(True)
        self.menu_action_verify_installation = QAction(MainWindow)
        self.menu_action_verify_installation.setObjectName(u"menu_action_verify_installation")
        self.menu_action_audible_generation_alert = QAction(MainWindow)
        self.menu_action_audible_generation_alert.setObjectName(u"menu_action_audible_generation_alert")
        self.menu_action_audible_generation_alert.setCheckable(True)
        self.menu_action_audible_generation_alert.setChecked(True)
        self.menu_action_visual_generation_alert = QAction(MainWindow)
        self.menu_action_visual_generation_alert.setObjectName(u"menu_action_visual_generation_alert")
        self.menu_action_visual_generation_alert.setCheckable(True)
        self.menu_action_visual_generation_alert.setChecked(True)
        self.menu_action_async_race = QAction(MainWindow)
        self.menu_action_async_race.setObjectName(u"menu_action_async_race")
        self.centralWidget = QWidget(MainWindow)
        self.centralWidget.setObjectName(u"centralWidget")
        self.centralWidget.setMaximumSize(QSize(16777215, 16777215))
        self.root_layout = QVBoxLayout(self.centralWidget)
        self.root_layout.setSpacing(6)
        self.root_layout.setContentsMargins(11, 11, 11, 11)
        self.root_layout.setObjectName(u"root_layout")
        self.root_layout.setContentsMargins(0, -1, 0, 0)
        self.main_tab_widget = QTabWidget(self.centralWidget)
        self.main_tab_widget.setObjectName(u"main_tab_widget")
        self.tab_welcome = QWidget()
        self.tab_welcome.setObjectName(u"tab_welcome")
        self.welcome_layout = QGridLayout(self.tab_welcome)
        self.welcome_layout.setSpacing(6)
        self.welcome_layout.setContentsMargins(11, 11, 11, 11)
        self.welcome_layout.setObjectName(u"welcome_layout")
        self.welcome_layout.setContentsMargins(4, 4, 4, 0)
        self.intro_play_multiworld_button = QPushButton(self.tab_welcome)
        self.intro_play_multiworld_button.setObjectName(u"intro_play_multiworld_button")
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.intro_play_multiworld_button.setFont(font)

        self.welcome_layout.addWidget(self.intro_play_multiworld_button, 3, 2, 1, 1)

        self.intro_play_existing_button = QPushButton(self.tab_welcome)
        self.intro_play_existing_button.setObjectName(u"intro_play_existing_button")
        self.intro_play_existing_button.setFont(font)

        self.welcome_layout.addWidget(self.intro_play_existing_button, 3, 0, 1, 1)

        self.intro_play_solo_button = QPushButton(self.tab_welcome)
        self.intro_play_solo_button.setObjectName(u"intro_play_solo_button")
        font1 = QFont()
        font1.setPointSize(14)
        font1.setBold(True)
        self.intro_play_solo_button.setFont(font1)

        self.welcome_layout.addWidget(self.intro_play_solo_button, 3, 1, 1, 1)

        self.intro_label = QLabel(self.tab_welcome)
        self.intro_label.setObjectName(u"intro_label")
        self.intro_label.setTextFormat(Qt.TextFormat.MarkdownText)
        self.intro_label.setScaledContents(False)
        self.intro_label.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.intro_label.setWordWrap(True)
        self.intro_label.setMargin(7)
        self.intro_label.setIndent(-1)
        self.intro_label.setOpenExternalLinks(False)

        self.welcome_layout.addWidget(self.intro_label, 0, 0, 1, 3)

        self.intro_welcome_label = QLabel(self.tab_welcome)
        self.intro_welcome_label.setObjectName(u"intro_welcome_label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.intro_welcome_label.sizePolicy().hasHeightForWidth())
        self.intro_welcome_label.setSizePolicy(sizePolicy)
        self.intro_welcome_label.setTextFormat(Qt.TextFormat.MarkdownText)
        self.intro_welcome_label.setWordWrap(True)

        self.welcome_layout.addWidget(self.intro_welcome_label, 1, 0, 1, 3)

        self.intro_vertical_spacer = QSpacerItem(20, 30, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.welcome_layout.addItem(self.intro_vertical_spacer, 2, 1, 1, 1)

        self.intro_top_spacer = QSpacerItem(20, 30, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.welcome_layout.addItem(self.intro_top_spacer, 4, 1, 1, 1)

        self.main_tab_widget.addTab(self.tab_welcome, "")
        self.tab_game_list = QScrollArea()
        self.tab_game_list.setObjectName(u"tab_game_list")
        self.tab_game_list.setWidgetResizable(True)
        self.game_list_contents = QWidget()
        self.game_list_contents.setObjectName(u"game_list_contents")
        self.game_list_contents.setGeometry(QRect(0, 0, 98, 28))
        self.tab_game_list.setWidget(self.game_list_contents)
        self.main_tab_widget.addTab(self.tab_game_list, "")
        self.tab_game_details = GamesHelpWidget()
        self.tab_game_details.setObjectName(u"tab_game_details")
        self.main_tab_widget.addTab(self.tab_game_details, "")
        self.tab_play_existing = QWidget()
        self.tab_play_existing.setObjectName(u"tab_play_existing")
        self.play_existing_layout = QVBoxLayout(self.tab_play_existing)
        self.play_existing_layout.setSpacing(6)
        self.play_existing_layout.setContentsMargins(11, 11, 11, 11)
        self.play_existing_layout.setObjectName(u"play_existing_layout")
        self.import_permalink_label = QLabel(self.tab_play_existing)
        self.import_permalink_label.setObjectName(u"import_permalink_label")
        self.import_permalink_label.setWordWrap(True)

        self.play_existing_layout.addWidget(self.import_permalink_label)

        self.import_permalink_button = QPushButton(self.tab_play_existing)
        self.import_permalink_button.setObjectName(u"import_permalink_button")

        self.play_existing_layout.addWidget(self.import_permalink_button)

        self.browse_racetime_label = QLabel(self.tab_play_existing)
        self.browse_racetime_label.setObjectName(u"browse_racetime_label")
        self.browse_racetime_label.setTextFormat(Qt.TextFormat.AutoText)
        self.browse_racetime_label.setWordWrap(True)
        self.browse_racetime_label.setOpenExternalLinks(True)

        self.play_existing_layout.addWidget(self.browse_racetime_label)

        self.browse_racetime_button = QPushButton(self.tab_play_existing)
        self.browse_racetime_button.setObjectName(u"browse_racetime_button")

        self.play_existing_layout.addWidget(self.browse_racetime_button)

        self.browse_async_races_label = QLabel(self.tab_play_existing)
        self.browse_async_races_label.setObjectName(u"browse_async_races_label")
        self.browse_async_races_label.setTextFormat(Qt.TextFormat.MarkdownText)

        self.play_existing_layout.addWidget(self.browse_async_races_label)

        self.browse_async_races_button = QPushButton(self.tab_play_existing)
        self.browse_async_races_button.setObjectName(u"browse_async_races_button")

        self.play_existing_layout.addWidget(self.browse_async_races_button)

        self.import_game_file_label = QLabel(self.tab_play_existing)
        self.import_game_file_label.setObjectName(u"import_game_file_label")
        self.import_game_file_label.setWordWrap(True)

        self.play_existing_layout.addWidget(self.import_game_file_label)

        self.import_game_file_button = QPushButton(self.tab_play_existing)
        self.import_game_file_button.setObjectName(u"import_game_file_button")

        self.play_existing_layout.addWidget(self.import_game_file_button)

        self.main_tab_widget.addTab(self.tab_play_existing, "")
        self.tab_multiworld = QWidget()
        self.tab_multiworld.setObjectName(u"tab_multiworld")
        self.verticalLayout = QVBoxLayout(self.tab_multiworld)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.multiworld_intro_label = QLabel(self.tab_multiworld)
        self.multiworld_intro_label.setObjectName(u"multiworld_intro_label")
        self.multiworld_intro_label.setTextFormat(Qt.TextFormat.MarkdownText)
        self.multiworld_intro_label.setWordWrap(True)

        self.verticalLayout.addWidget(self.multiworld_intro_label)

        self.multiworld_line = QFrame(self.tab_multiworld)
        self.multiworld_line.setObjectName(u"multiworld_line")
        self.multiworld_line.setFrameShape(QFrame.Shape.HLine)
        self.multiworld_line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.multiworld_line)

        self.browse_sessions_label = QLabel(self.tab_multiworld)
        self.browse_sessions_label.setObjectName(u"browse_sessions_label")
        self.browse_sessions_label.setWordWrap(True)

        self.verticalLayout.addWidget(self.browse_sessions_label)

        self.browse_sessions_button = QPushButton(self.tab_multiworld)
        self.browse_sessions_button.setObjectName(u"browse_sessions_button")

        self.verticalLayout.addWidget(self.browse_sessions_button)

        self.host_new_game_label = QLabel(self.tab_multiworld)
        self.host_new_game_label.setObjectName(u"host_new_game_label")
        self.host_new_game_label.setWordWrap(True)

        self.verticalLayout.addWidget(self.host_new_game_label)

        self.host_new_game_button = QPushButton(self.tab_multiworld)
        self.host_new_game_button.setObjectName(u"host_new_game_button")

        self.verticalLayout.addWidget(self.host_new_game_button)

        self.game_connection_line = QFrame(self.tab_multiworld)
        self.game_connection_line.setObjectName(u"game_connection_line")
        self.game_connection_line.setFrameShape(QFrame.Shape.HLine)
        self.game_connection_line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.game_connection_line)

        self.game_connection_label = QLabel(self.tab_multiworld)
        self.game_connection_label.setObjectName(u"game_connection_label")

        self.verticalLayout.addWidget(self.game_connection_label)

        self.game_connection_button = QPushButton(self.tab_multiworld)
        self.game_connection_button.setObjectName(u"game_connection_button")

        self.verticalLayout.addWidget(self.game_connection_button)

        self.main_tab_widget.addTab(self.tab_multiworld, "")

        self.root_layout.addWidget(self.main_tab_widget)

        self.progress_bar = QProgressBar(self.centralWidget)
        self.progress_bar.setObjectName(u"progress_bar")
        self.progress_bar.setMinimumSize(QSize(150, 0))
        self.progress_bar.setMaximumSize(QSize(150, 16777215))
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setInvertedAppearance(False)

        self.root_layout.addWidget(self.progress_bar)

        self.stop_background_process_button = QPushButton(self.centralWidget)
        self.stop_background_process_button.setObjectName(u"stop_background_process_button")
        self.stop_background_process_button.setEnabled(False)
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.stop_background_process_button.sizePolicy().hasHeightForWidth())
        self.stop_background_process_button.setSizePolicy(sizePolicy1)
        self.stop_background_process_button.setMaximumSize(QSize(75, 16777215))
        self.stop_background_process_button.setCheckable(False)
        self.stop_background_process_button.setFlat(False)

        self.root_layout.addWidget(self.stop_background_process_button)

        self.progress_label = QLabel(self.centralWidget)
        self.progress_label.setObjectName(u"progress_label")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.progress_label.sizePolicy().hasHeightForWidth())
        self.progress_label.setSizePolicy(sizePolicy2)
        font2 = QFont()
        font2.setPointSize(7)
        self.progress_label.setFont(font2)
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.progress_label.setWordWrap(True)

        self.root_layout.addWidget(self.progress_label)

        MainWindow.setCentralWidget(self.centralWidget)
        self.status_bar = QStatusBar(MainWindow)
        self.status_bar.setObjectName(u"status_bar")
        MainWindow.setStatusBar(self.status_bar)
        self.menu_bar = QMenuBar(MainWindow)
        self.menu_bar.setObjectName(u"menu_bar")
        self.menu_bar.setGeometry(QRect(0, 0, 688, 17))
        self.menu_open = QMenu(self.menu_bar)
        self.menu_open.setObjectName(u"menu_open")
        self.menu_edit = QMenu(self.menu_bar)
        self.menu_edit.setObjectName(u"menu_edit")
        self.menu_database = QMenu(self.menu_edit)
        self.menu_database.setObjectName(u"menu_database")
        self.menu_internal = QMenu(self.menu_database)
        self.menu_internal.setObjectName(u"menu_internal")
        self.menu_preferences = QMenu(self.menu_bar)
        self.menu_preferences.setObjectName(u"menu_preferences")
        self.menu_advanced = QMenu(self.menu_preferences)
        self.menu_advanced.setObjectName(u"menu_advanced")
        self.menu_alert_when_generation_completes = QMenu(self.menu_preferences)
        self.menu_alert_when_generation_completes.setObjectName(u"menu_alert_when_generation_completes")
        self.menu_alert_when_generation_completes.setToolTipsVisible(False)
        self.menu_help = QMenu(self.menu_bar)
        self.menu_help.setObjectName(u"menu_help")
        self.menu_create = QMenu(self.menu_bar)
        self.menu_create.setObjectName(u"menu_create")
        MainWindow.setMenuBar(self.menu_bar)

        self.menu_bar.addAction(self.menu_open.menuAction())
        self.menu_bar.addAction(self.menu_edit.menuAction())
        self.menu_bar.addAction(self.menu_create.menuAction())
        self.menu_bar.addAction(self.menu_preferences.menuAction())
        self.menu_bar.addAction(self.menu_help.menuAction())
        self.menu_open.addAction(self.menu_action_previously_generated_games)
        self.menu_open.addAction(self.menu_action_log_files_directory)
        self.menu_open.addSeparator()
        self.menu_open.addAction(self.menu_action_login_window)
        self.menu_open.addAction(self.menu_action_open_auto_tracker)
        self.menu_open.addSeparator()
        self.menu_open.addSeparator()
        self.menu_edit.addAction(self.menu_database.menuAction())
        self.menu_database.addAction(self.menu_internal.menuAction())
        self.menu_database.addAction(self.menu_action_edit_existing_database)
        self.menu_preferences.addAction(self.menu_action_dark_mode)
        self.menu_preferences.addAction(self.menu_action_show_multiworld_banner)
        self.menu_preferences.addAction(self.menu_action_experimental_settings)
        self.menu_preferences.addAction(self.menu_alert_when_generation_completes.menuAction())
        self.menu_preferences.addAction(self.menu_action_automatic_reporting)
        self.menu_preferences.addSeparator()
        self.menu_preferences.addSeparator()
        self.menu_preferences.addAction(self.menu_advanced.menuAction())
        self.menu_advanced.addAction(self.menu_action_validate_seed_after)
        self.menu_advanced.addAction(self.menu_action_timeout_generation_after_a_time_limit)
        self.menu_advanced.addAction(self.menu_action_generate_in_another_process)
        self.menu_alert_when_generation_completes.addAction(self.menu_action_audible_generation_alert)
        self.menu_alert_when_generation_completes.addAction(self.menu_action_visual_generation_alert)
        self.menu_help.addAction(self.menu_action_help)
        self.menu_help.addAction(self.menu_action_changelog)
        self.menu_help.addAction(self.menu_action_verify_installation)
        self.menu_help.addSeparator()
        self.menu_help.addAction(self.menu_action_dependencies)
        self.menu_help.addAction(self.menu_action_about)
        self.menu_create.addAction(self.menu_action_async_race)

        self.retranslateUi(MainWindow)

        self.main_tab_widget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Randovania", None))
        self.menu_action_edit_existing_database.setText(QCoreApplication.translate("MainWindow", u"External file", None))
        self.menu_action_validate_seed_after.setText(QCoreApplication.translate("MainWindow", u"Validate if a game is possible after generation", None))
        self.menu_action_timeout_generation_after_a_time_limit.setText(QCoreApplication.translate("MainWindow", u"Timeout generation after a time limit", None))
        self.menu_action_open_auto_tracker.setText(QCoreApplication.translate("MainWindow", u"Automatic Item Tracker", None))
        self.menu_action_login_window.setText(QCoreApplication.translate("MainWindow", u"Login", None))
        self.menu_action_dark_mode.setText(QCoreApplication.translate("MainWindow", u"Dark Mode", None))
        self.menu_action_show_multiworld_banner.setText(QCoreApplication.translate("MainWindow", u"Show Multiworld Banner", None))
        self.menu_action_previously_generated_games.setText(QCoreApplication.translate("MainWindow", u"Previously generated games", None))
        self.menu_action_log_files_directory.setText(QCoreApplication.translate("MainWindow", u"Log files folder", None))
        self.menu_action_help.setText(QCoreApplication.translate("MainWindow", u"Randovania Help", None))
        self.menu_action_changelog.setText(QCoreApplication.translate("MainWindow", u"Change Log", None))
        self.menu_action_about.setText(QCoreApplication.translate("MainWindow", u"About", None))
        self.menu_action_dependencies.setText(QCoreApplication.translate("MainWindow", u"Dependencies", None))
        self.menu_action_experimental_settings.setText(QCoreApplication.translate("MainWindow", u"Show Experimental Settings", None))
        self.menu_action_automatic_reporting.setText(QCoreApplication.translate("MainWindow", u"Automatic Data Collection and Reporting", None))
        self.menu_action_generate_in_another_process.setText(QCoreApplication.translate("MainWindow", u"Generate games in another process", None))
        self.menu_action_verify_installation.setText(QCoreApplication.translate("MainWindow", u"Verify installation", None))
        self.menu_action_audible_generation_alert.setText(QCoreApplication.translate("MainWindow", u"Audible Sound Alert", None))
        self.menu_action_visual_generation_alert.setText(QCoreApplication.translate("MainWindow", u"Visual Taskbar Alert", None))
        self.menu_action_async_race.setText(QCoreApplication.translate("MainWindow", u"Async Race", None))
        self.intro_play_multiworld_button.setText(QCoreApplication.translate("MainWindow", u"Play a multiworld", None))
        self.intro_play_existing_button.setText(QCoreApplication.translate("MainWindow", u"Import a game", None))
        self.intro_play_solo_button.setText(QCoreApplication.translate("MainWindow", u"Play a new solo game", None))
        self.intro_label.setText(QCoreApplication.translate("MainWindow", u"Welcome to Randovania {version}, a randomizer for a multitude of games.", None))
        self.main_tab_widget.setTabText(self.main_tab_widget.indexOf(self.tab_welcome), QCoreApplication.translate("MainWindow", u"Welcome", None))
        self.main_tab_widget.setTabText(self.main_tab_widget.indexOf(self.tab_game_list), QCoreApplication.translate("MainWindow", u"Games", None))
        self.main_tab_widget.setTabText(self.main_tab_widget.indexOf(self.tab_game_details), QCoreApplication.translate("MainWindow", u"Games", None))
        self.import_permalink_label.setText(QCoreApplication.translate("MainWindow", u"<html><head/><body><p>Are you playing with others?</p><p>Ask them for a permalink and import it here. You'll create the same game as them.</p></body></html>", None))
        self.import_permalink_button.setText(QCoreApplication.translate("MainWindow", u"Import permalink", None))
        self.browse_racetime_label.setText(QCoreApplication.translate("MainWindow", u"<html><head/><body><p>Are you joining a live race hosted in <a href=\"https://racetime.gg/\"><span style=\" text-decoration: underline; color:#0000ff;\">racetime.gg</span></a>?</p><p>Select the race from Randovania and automatically import the permalink!</p></body></html>", None))
        self.browse_racetime_button.setText(QCoreApplication.translate("MainWindow", u"Browse races in racetime.gg", None))
        self.browse_async_races_label.setText(QCoreApplication.translate("MainWindow", u"<html><head/><body><p>Are you joining an asynchronous race?</p><p>Browse through a list of these to join one directly from Randovania.</p></body></html>", None))
        self.browse_async_races_button.setText(QCoreApplication.translate("MainWindow", u"Browse asynchronous races", None))
        self.import_game_file_label.setText(QCoreApplication.translate("MainWindow", u"<html><head/><body><p>If they've shared a spoiler file instead, you can import it directly. This skips the generation step. You can also drag and drop the file into Randovania.</p></body></html>", None))
        self.import_game_file_button.setText(QCoreApplication.translate("MainWindow", u"Import game file", None))
        self.main_tab_widget.setTabText(self.main_tab_widget.indexOf(self.tab_play_existing), QCoreApplication.translate("MainWindow", u"Import Game", None))
        self.multiworld_intro_label.setText(QCoreApplication.translate("MainWindow", u"Multiworld is a game mode for the randomizer where multiple games and/or multiple players can come together to create a larger experience.\n"
"\n"
"For more information, check [Randovania Help](help://tab_multiworld)!", None))
        self.browse_sessions_label.setText(QCoreApplication.translate("MainWindow", u"<html><head/><body><p>Joining a multiworld that someone else created? Browse all existing sessions here!</p></body></html>", None))
        self.browse_sessions_button.setText(QCoreApplication.translate("MainWindow", u"Browse for a multiworld session", None))
        self.host_new_game_label.setText(QCoreApplication.translate("MainWindow", u"<html><head/><body><p>Want to play multiworld?</p><p>Host a new online session and invite people!</p></body></html>", None))
        self.host_new_game_button.setText(QCoreApplication.translate("MainWindow", u"Host new multiworld session", None))
        self.game_connection_label.setText(QCoreApplication.translate("MainWindow", u"Connect Randovania to the many games it support, enabling multiworld or maybe just an automatic tracker.", None))
        self.game_connection_button.setText(QCoreApplication.translate("MainWindow", u"Connect to games", None))
        self.main_tab_widget.setTabText(self.main_tab_widget.indexOf(self.tab_multiworld), QCoreApplication.translate("MainWindow", u"Multiworld", None))
        self.stop_background_process_button.setText(QCoreApplication.translate("MainWindow", u"Stop", None))
        self.progress_label.setText("")
        self.menu_open.setTitle(QCoreApplication.translate("MainWindow", u"Open", None))
        self.menu_edit.setTitle(QCoreApplication.translate("MainWindow", u"Edit", None))
        self.menu_database.setTitle(QCoreApplication.translate("MainWindow", u"Database", None))
        self.menu_internal.setTitle(QCoreApplication.translate("MainWindow", u"Internal", None))
        self.menu_preferences.setTitle(QCoreApplication.translate("MainWindow", u"Preferences", None))
        self.menu_advanced.setTitle(QCoreApplication.translate("MainWindow", u"Advanced", None))
        self.menu_alert_when_generation_completes.setTitle(QCoreApplication.translate("MainWindow", u"Alert When Generation Completes", None))
        self.menu_help.setTitle(QCoreApplication.translate("MainWindow", u"Help", None))
        self.menu_create.setTitle(QCoreApplication.translate("MainWindow", u"Create", None))
    # retranslateUi

