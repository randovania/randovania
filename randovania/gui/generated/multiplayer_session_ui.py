# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'multiplayer_session.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QCheckBox, QComboBox,
    QGridLayout, QGroupBox, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QMainWindow, QMenuBar,
    QProgressBar, QPushButton, QSizePolicy, QSpacerItem,
    QTabWidget, QTableView, QVBoxLayout, QWidget)

class Ui_MultiplayerSessionWindow(object):
    def setupUi(self, MultiplayerSessionWindow):
        if not MultiplayerSessionWindow.objectName():
            MultiplayerSessionWindow.setObjectName(u"MultiplayerSessionWindow")
        MultiplayerSessionWindow.resize(773, 458)
        MultiplayerSessionWindow.setDockNestingEnabled(True)
        self.action_add_player = QAction(MultiplayerSessionWindow)
        self.action_add_player.setObjectName(u"action_add_player")
        self.action_add_row = QAction(MultiplayerSessionWindow)
        self.action_add_row.setObjectName(u"action_add_row")
        self.rename_session_action = QAction(MultiplayerSessionWindow)
        self.rename_session_action.setObjectName(u"rename_session_action")
        self.change_password_action = QAction(MultiplayerSessionWindow)
        self.change_password_action.setObjectName(u"change_password_action")
        self.delete_session_action = QAction(MultiplayerSessionWindow)
        self.delete_session_action.setObjectName(u"delete_session_action")
        self.actionbar = QAction(MultiplayerSessionWindow)
        self.actionbar.setObjectName(u"actionbar")
        self.actionasdf = QAction(MultiplayerSessionWindow)
        self.actionasdf.setObjectName(u"actionasdf")
        self.central_widget = QWidget(MultiplayerSessionWindow)
        self.central_widget.setObjectName(u"central_widget")
        self.central_widget.setMaximumSize(QSize(16777215, 16777215))
        self.verticalLayout = QVBoxLayout(self.central_widget)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.tab_widget = QTabWidget(self.central_widget)
        self.tab_widget.setObjectName(u"tab_widget")
        self.tab_worlds = QWidget()
        self.tab_worlds.setObjectName(u"tab_worlds")
        self.worlds_layout = QVBoxLayout(self.tab_worlds)
        self.worlds_layout.setSpacing(6)
        self.worlds_layout.setContentsMargins(11, 11, 11, 11)
        self.worlds_layout.setObjectName(u"worlds_layout")
        self.worlds_layout.setContentsMargins(0, 0, 0, -1)
        self.not_connected_warning_label = QLabel(self.tab_worlds)
        self.not_connected_warning_label.setObjectName(u"not_connected_warning_label")
        self.not_connected_warning_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.not_connected_warning_label.setWordWrap(True)

        self.worlds_layout.addWidget(self.not_connected_warning_label)

        self.generate_game_label = QLabel(self.tab_worlds)
        self.generate_game_label.setObjectName(u"generate_game_label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.generate_game_label.sizePolicy().hasHeightForWidth())
        self.generate_game_label.setSizePolicy(sizePolicy)
        self.generate_game_label.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByMouse|Qt.TextInteractionFlag.TextSelectableByMouse)

        self.worlds_layout.addWidget(self.generate_game_label)

        self.generate_game_layout = QHBoxLayout()
        self.generate_game_layout.setSpacing(6)
        self.generate_game_layout.setObjectName(u"generate_game_layout")
        self.generate_game_button = QPushButton(self.tab_worlds)
        self.generate_game_button.setObjectName(u"generate_game_button")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.generate_game_button.sizePolicy().hasHeightForWidth())
        self.generate_game_button.setSizePolicy(sizePolicy1)

        self.generate_game_layout.addWidget(self.generate_game_button)

        self.export_game_button = QPushButton(self.tab_worlds)
        self.export_game_button.setObjectName(u"export_game_button")

        self.generate_game_layout.addWidget(self.export_game_button)


        self.worlds_layout.addLayout(self.generate_game_layout)

        self.tab_widget.addTab(self.tab_worlds, "")
        self.tab_session = QWidget()
        self.tab_session.setObjectName(u"tab_session")
        self.session_tab_layout = QGridLayout(self.tab_session)
        self.session_tab_layout.setSpacing(6)
        self.session_tab_layout.setContentsMargins(11, 11, 11, 11)
        self.session_tab_layout.setObjectName(u"session_tab_layout")
        self.session_admin_group = QGroupBox(self.tab_session)
        self.session_admin_group.setObjectName(u"session_admin_group")
        self.session_admin_layout = QGridLayout(self.session_admin_group)
        self.session_admin_layout.setSpacing(6)
        self.session_admin_layout.setContentsMargins(11, 11, 11, 11)
        self.session_admin_layout.setObjectName(u"session_admin_layout")
        self.advanced_options_tool = QPushButton(self.session_admin_group)
        self.advanced_options_tool.setObjectName(u"advanced_options_tool")
        sizePolicy1.setHeightForWidth(self.advanced_options_tool.sizePolicy().hasHeightForWidth())
        self.advanced_options_tool.setSizePolicy(sizePolicy1)

        self.session_admin_layout.addWidget(self.advanced_options_tool, 1, 1, 1, 1)

        self.copy_permalink_button = QPushButton(self.session_admin_group)
        self.copy_permalink_button.setObjectName(u"copy_permalink_button")

        self.session_admin_layout.addWidget(self.copy_permalink_button, 1, 0, 1, 1)

        self.session_visibility_button = QPushButton(self.session_admin_group)
        self.session_visibility_button.setObjectName(u"session_visibility_button")

        self.session_admin_layout.addWidget(self.session_visibility_button, 0, 1, 1, 1)

        self.view_game_details_button = QPushButton(self.session_admin_group)
        self.view_game_details_button.setObjectName(u"view_game_details_button")

        self.session_admin_layout.addWidget(self.view_game_details_button, 0, 0, 1, 1)

        self.everyone_can_claim_check = QCheckBox(self.session_admin_group)
        self.everyone_can_claim_check.setObjectName(u"everyone_can_claim_check")

        self.session_admin_layout.addWidget(self.everyone_can_claim_check, 2, 0, 1, 1)

        self.allow_coop_check = QCheckBox(self.session_admin_group)
        self.allow_coop_check.setObjectName(u"allow_coop_check")

        self.session_admin_layout.addWidget(self.allow_coop_check, 3, 0, 1, 1)


        self.session_tab_layout.addWidget(self.session_admin_group, 0, 0, 1, 2)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.session_tab_layout.addItem(self.verticalSpacer, 3, 0, 1, 2)

        self.connectivity_group = QGroupBox(self.tab_session)
        self.connectivity_group.setObjectName(u"connectivity_group")
        self.connectivity_layout = QGridLayout(self.connectivity_group)
        self.connectivity_layout.setSpacing(6)
        self.connectivity_layout.setContentsMargins(11, 11, 11, 11)
        self.connectivity_layout.setObjectName(u"connectivity_layout")
        self.server_connection_button = QPushButton(self.connectivity_group)
        self.server_connection_button.setObjectName(u"server_connection_button")

        self.connectivity_layout.addWidget(self.server_connection_button, 1, 0, 1, 1)

        self.edit_game_connections_button = QPushButton(self.connectivity_group)
        self.edit_game_connections_button.setObjectName(u"edit_game_connections_button")

        self.connectivity_layout.addWidget(self.edit_game_connections_button, 1, 1, 1, 1)

        self.server_connection_label = QLabel(self.connectivity_group)
        self.server_connection_label.setObjectName(u"server_connection_label")

        self.connectivity_layout.addWidget(self.server_connection_label, 0, 0, 1, 1)

        self.multiworld_client_status_label = QLabel(self.connectivity_group)
        self.multiworld_client_status_label.setObjectName(u"multiworld_client_status_label")
        self.multiworld_client_status_label.setTextFormat(Qt.TextFormat.MarkdownText)
        self.multiworld_client_status_label.setWordWrap(True)

        self.connectivity_layout.addWidget(self.multiworld_client_status_label, 2, 0, 1, 2)


        self.session_tab_layout.addWidget(self.connectivity_group, 1, 0, 1, 2)

        self.tab_widget.addTab(self.tab_session, "")
        self.tab_history = QWidget()
        self.tab_history.setObjectName(u"tab_history")
        self.history_layout = QVBoxLayout(self.tab_history)
        self.history_layout.setSpacing(6)
        self.history_layout.setContentsMargins(11, 11, 11, 11)
        self.history_layout.setObjectName(u"history_layout")
        self.history_layout.setContentsMargins(0, -1, 0, 0)
        self.history_filter_layout = QHBoxLayout()
        self.history_filter_layout.setSpacing(6)
        self.history_filter_layout.setObjectName(u"history_filter_layout")
        self.history_filter_layout.setContentsMargins(4, -1, 4, -1)
        self.history_filter_provider_combo = QComboBox(self.tab_history)
        self.history_filter_provider_combo.addItem("")
        self.history_filter_provider_combo.setObjectName(u"history_filter_provider_combo")

        self.history_filter_layout.addWidget(self.history_filter_provider_combo)

        self.history_filter_receiver_combo = QComboBox(self.tab_history)
        self.history_filter_receiver_combo.addItem("")
        self.history_filter_receiver_combo.setObjectName(u"history_filter_receiver_combo")

        self.history_filter_layout.addWidget(self.history_filter_receiver_combo)

        self.history_filter_edit = QLineEdit(self.tab_history)
        self.history_filter_edit.setObjectName(u"history_filter_edit")

        self.history_filter_layout.addWidget(self.history_filter_edit)


        self.history_layout.addLayout(self.history_filter_layout)

        self.history_view = QTableView(self.tab_history)
        self.history_view.setObjectName(u"history_view")
        self.history_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.history_view.setSortingEnabled(True)

        self.history_layout.addWidget(self.history_view)

        self.tab_widget.addTab(self.tab_history, "")
        self.tab_audit = QTableView()
        self.tab_audit.setObjectName(u"tab_audit")
        self.tab_audit.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tab_audit.setSortingEnabled(True)
        self.tab_widget.addTab(self.tab_audit, "")

        self.verticalLayout.addWidget(self.tab_widget)

        self.progress_label = QLabel(self.central_widget)
        self.progress_label.setObjectName(u"progress_label")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.progress_label.sizePolicy().hasHeightForWidth())
        self.progress_label.setSizePolicy(sizePolicy2)
        self.progress_label.setTextFormat(Qt.TextFormat.MarkdownText)
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.progress_label.setWordWrap(True)
        self.progress_label.setOpenExternalLinks(True)

        self.verticalLayout.addWidget(self.progress_label)

        self.background_process_layout = QHBoxLayout()
        self.background_process_layout.setSpacing(6)
        self.background_process_layout.setObjectName(u"background_process_layout")
        self.background_process_button = QPushButton(self.central_widget)
        self.background_process_button.setObjectName(u"background_process_button")
        self.background_process_button.setMinimumSize(QSize(140, 0))

        self.background_process_layout.addWidget(self.background_process_button)

        self.progress_bar = QProgressBar(self.central_widget)
        self.progress_bar.setObjectName(u"progress_bar")
        self.progress_bar.setValue(0)
        self.progress_bar.setInvertedAppearance(False)

        self.background_process_layout.addWidget(self.progress_bar)


        self.verticalLayout.addLayout(self.background_process_layout)

        MultiplayerSessionWindow.setCentralWidget(self.central_widget)
        self.menu_bar = QMenuBar(MultiplayerSessionWindow)
        self.menu_bar.setObjectName(u"menu_bar")
        self.menu_bar.setGeometry(QRect(0, 0, 773, 23))
        MultiplayerSessionWindow.setMenuBar(self.menu_bar)

        self.retranslateUi(MultiplayerSessionWindow)

        self.tab_widget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MultiplayerSessionWindow)
    # setupUi

    def retranslateUi(self, MultiplayerSessionWindow):
        MultiplayerSessionWindow.setWindowTitle(QCoreApplication.translate("MultiplayerSessionWindow", u"Multiworld Session", None))
        self.action_add_player.setText(QCoreApplication.translate("MultiplayerSessionWindow", u"Add player", None))
        self.action_add_row.setText(QCoreApplication.translate("MultiplayerSessionWindow", u"Add row", None))
        self.rename_session_action.setText(QCoreApplication.translate("MultiplayerSessionWindow", u"Change title", None))
        self.change_password_action.setText(QCoreApplication.translate("MultiplayerSessionWindow", u"Change password", None))
        self.delete_session_action.setText(QCoreApplication.translate("MultiplayerSessionWindow", u"Delete session", None))
        self.actionbar.setText(QCoreApplication.translate("MultiplayerSessionWindow", u"bar", None))
        self.actionasdf.setText(QCoreApplication.translate("MultiplayerSessionWindow", u"asdf", None))
        self.not_connected_warning_label.setText(QCoreApplication.translate("MultiplayerSessionWindow", u"TextLabel", None))
        self.generate_game_label.setText(QCoreApplication.translate("MultiplayerSessionWindow", u"<Game not generated>", None))
        self.generate_game_button.setText(QCoreApplication.translate("MultiplayerSessionWindow", u"Generate Game", None))
        self.export_game_button.setText(QCoreApplication.translate("MultiplayerSessionWindow", u"Export Game", None))
        self.tab_widget.setTabText(self.tab_widget.indexOf(self.tab_worlds), QCoreApplication.translate("MultiplayerSessionWindow", u"Users and Worlds", None))
        self.session_admin_group.setTitle(QCoreApplication.translate("MultiplayerSessionWindow", u"Session Administration", None))
        self.advanced_options_tool.setText(QCoreApplication.translate("MultiplayerSessionWindow", u"Advanced options...", None))
        self.copy_permalink_button.setText(QCoreApplication.translate("MultiplayerSessionWindow", u"Copy Permalink", None))
        self.session_visibility_button.setText(QCoreApplication.translate("MultiplayerSessionWindow", u"Start", None))
        self.view_game_details_button.setText(QCoreApplication.translate("MultiplayerSessionWindow", u"View Spoiler", None))
        self.everyone_can_claim_check.setText(QCoreApplication.translate("MultiplayerSessionWindow", u"Everyone can claim worlds", None))
        self.allow_coop_check.setText(QCoreApplication.translate("MultiplayerSessionWindow", u"Enable Co-Op", None))
        self.connectivity_group.setTitle(QCoreApplication.translate("MultiplayerSessionWindow", u"Connectivity", None))
        self.server_connection_button.setText(QCoreApplication.translate("MultiplayerSessionWindow", u"Connect to Server", None))
        self.edit_game_connections_button.setText(QCoreApplication.translate("MultiplayerSessionWindow", u"Edit Game Connections", None))
        self.server_connection_label.setText(QCoreApplication.translate("MultiplayerSessionWindow", u"Server: Disconnected", None))
        self.multiworld_client_status_label.setText("")
        self.tab_widget.setTabText(self.tab_widget.indexOf(self.tab_session), QCoreApplication.translate("MultiplayerSessionWindow", u"Session and Connectivity", None))
        self.history_filter_provider_combo.setItemText(0, QCoreApplication.translate("MultiplayerSessionWindow", u"All Worlds", None))

        self.history_filter_receiver_combo.setItemText(0, QCoreApplication.translate("MultiplayerSessionWindow", u"All Worlds", None))

        self.history_filter_edit.setPlaceholderText(QCoreApplication.translate("MultiplayerSessionWindow", u"Filter by pickup or location", None))
        self.tab_widget.setTabText(self.tab_widget.indexOf(self.tab_history), QCoreApplication.translate("MultiplayerSessionWindow", u"History", None))
        self.tab_widget.setTabText(self.tab_widget.indexOf(self.tab_audit), QCoreApplication.translate("MultiplayerSessionWindow", u"Audit Log", None))
        self.progress_label.setText("")
        self.background_process_button.setText(QCoreApplication.translate("MultiplayerSessionWindow", u"Stop", None))
    # retranslateUi

