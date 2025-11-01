# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'msr_game_export_dialog.ui'
##
## Created by: Qt User Interface Compiler version 6.10.0
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
from PySide6.QtWidgets import (QApplication, QButtonGroup, QCheckBox, QComboBox,
    QDialog, QFrame, QGridLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QRadioButton,
    QSizePolicy, QTabWidget, QVBoxLayout, QWidget)

class Ui_MSRGameExportDialog(object):
    def setupUi(self, MSRGameExportDialog):
        if not MSRGameExportDialog.objectName():
            MSRGameExportDialog.setObjectName(u"MSRGameExportDialog")
        MSRGameExportDialog.resize(501, 399)
        self.root_layout = QGridLayout(MSRGameExportDialog)
        self.root_layout.setSpacing(6)
        self.root_layout.setContentsMargins(11, 11, 11, 11)
        self.root_layout.setObjectName(u"root_layout")
        self.input_file_label = QLabel(MSRGameExportDialog)
        self.input_file_label.setObjectName(u"input_file_label")
        self.input_file_label.setMaximumSize(QSize(16777215, 16777215))
        self.input_file_label.setWordWrap(True)

        self.root_layout.addWidget(self.input_file_label, 0, 0, 1, 3)

        self.input_file_button = QPushButton(MSRGameExportDialog)
        self.input_file_button.setObjectName(u"input_file_button")
        self.input_file_button.setMaximumSize(QSize(100, 16777215))

        self.root_layout.addWidget(self.input_file_button, 1, 2, 1, 1)

        self.input_file_edit = QLineEdit(MSRGameExportDialog)
        self.input_file_edit.setObjectName(u"input_file_edit")

        self.root_layout.addWidget(self.input_file_edit, 1, 0, 1, 2)

        self.accept_button = QPushButton(MSRGameExportDialog)
        self.accept_button.setObjectName(u"accept_button")

        self.root_layout.addWidget(self.accept_button, 14, 0, 1, 1)

        self.target_platform_layout = QHBoxLayout()
        self.target_platform_layout.setSpacing(6)
        self.target_platform_layout.setObjectName(u"target_platform_layout")
        self.target_platform_layout.setContentsMargins(-1, 0, -1, -1)
        self.target_platform_label = QLabel(MSRGameExportDialog)
        self.target_platform_label.setObjectName(u"target_platform_label")

        self.target_platform_layout.addWidget(self.target_platform_label)

        self.luma_radio = QRadioButton(MSRGameExportDialog)
        self.platform_btn_group = QButtonGroup(MSRGameExportDialog)
        self.platform_btn_group.setObjectName(u"platform_btn_group")
        self.platform_btn_group.addButton(self.luma_radio)
        self.luma_radio.setObjectName(u"luma_radio")

        self.target_platform_layout.addWidget(self.luma_radio)

        self.azahar_radio = QRadioButton(MSRGameExportDialog)
        self.platform_btn_group.addButton(self.azahar_radio)
        self.azahar_radio.setObjectName(u"azahar_radio")

        self.target_platform_layout.addWidget(self.azahar_radio)


        self.root_layout.addLayout(self.target_platform_layout, 7, 0, 1, 3)

        self.output_tab_widget = QTabWidget(MSRGameExportDialog)
        self.output_tab_widget.setObjectName(u"output_tab_widget")
        self.tab_sd_card = QWidget()
        self.tab_sd_card.setObjectName(u"tab_sd_card")
        self.verticalLayout = QVBoxLayout(self.tab_sd_card)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.sd_label = QLabel(self.tab_sd_card)
        self.sd_label.setObjectName(u"sd_label")

        self.verticalLayout.addWidget(self.sd_label)

        self.sd_driver_layout = QHBoxLayout()
        self.sd_driver_layout.setSpacing(6)
        self.sd_driver_layout.setObjectName(u"sd_driver_layout")
        self.sd_combo = QComboBox(self.tab_sd_card)
        self.sd_combo.addItem("")
        self.sd_combo.setObjectName(u"sd_combo")

        self.sd_driver_layout.addWidget(self.sd_combo)

        self.sd_non_removable = QCheckBox(self.tab_sd_card)
        self.sd_non_removable.setObjectName(u"sd_non_removable")

        self.sd_driver_layout.addWidget(self.sd_non_removable)

        self.sd_refresh_button = QPushButton(self.tab_sd_card)
        self.sd_refresh_button.setObjectName(u"sd_refresh_button")

        self.sd_driver_layout.addWidget(self.sd_refresh_button)


        self.verticalLayout.addLayout(self.sd_driver_layout)

        self.output_tab_widget.addTab(self.tab_sd_card, "")
        self.tab_ftp = QWidget()
        self.tab_ftp.setObjectName(u"tab_ftp")
        self.tab_ftp_layout = QGridLayout(self.tab_ftp)
        self.tab_ftp_layout.setSpacing(6)
        self.tab_ftp_layout.setContentsMargins(11, 11, 11, 11)
        self.tab_ftp_layout.setObjectName(u"tab_ftp_layout")
        self.ftp_description_label = QLabel(self.tab_ftp)
        self.ftp_description_label.setObjectName(u"ftp_description_label")
        self.ftp_description_label.setWordWrap(True)
        self.ftp_description_label.setOpenExternalLinks(True)

        self.tab_ftp_layout.addWidget(self.ftp_description_label, 0, 0, 1, 4)

        self.ftp_anonymous_check = QCheckBox(self.tab_ftp)
        self.ftp_anonymous_check.setObjectName(u"ftp_anonymous_check")

        self.tab_ftp_layout.addWidget(self.ftp_anonymous_check, 1, 0, 1, 1)

        self.ftp_username_edit = QLineEdit(self.tab_ftp)
        self.ftp_username_edit.setObjectName(u"ftp_username_edit")

        self.tab_ftp_layout.addWidget(self.ftp_username_edit, 1, 1, 1, 1)

        self.ftp_password_edit = QLineEdit(self.tab_ftp)
        self.ftp_password_edit.setObjectName(u"ftp_password_edit")

        self.tab_ftp_layout.addWidget(self.ftp_password_edit, 1, 2, 1, 2)

        self.ftp_ip_label = QLabel(self.tab_ftp)
        self.ftp_ip_label.setObjectName(u"ftp_ip_label")

        self.tab_ftp_layout.addWidget(self.ftp_ip_label, 2, 0, 1, 1)

        self.ftp_ip_edit = QLineEdit(self.tab_ftp)
        self.ftp_ip_edit.setObjectName(u"ftp_ip_edit")

        self.tab_ftp_layout.addWidget(self.ftp_ip_edit, 2, 1, 1, 1)

        self.ftp_port_edit = QLineEdit(self.tab_ftp)
        self.ftp_port_edit.setObjectName(u"ftp_port_edit")
        self.ftp_port_edit.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.tab_ftp_layout.addWidget(self.ftp_port_edit, 2, 2, 1, 1)

        self.ftp_test_button = QPushButton(self.tab_ftp)
        self.ftp_test_button.setObjectName(u"ftp_test_button")

        self.tab_ftp_layout.addWidget(self.ftp_test_button, 2, 3, 1, 1)

        self.output_tab_widget.addTab(self.tab_ftp, "")
        self.tab_azahar = QWidget()
        self.tab_azahar.setObjectName(u"tab_azahar")
        self.azahar_label = QLabel(self.tab_azahar)
        self.azahar_label.setObjectName(u"azahar_label")
        self.azahar_label.setGeometry(QRect(0, 0, 473, 171))
        self.azahar_label.setWordWrap(True)
        self.output_tab_widget.addTab(self.tab_azahar, "")
        self.tab_custom_path = QWidget()
        self.tab_custom_path.setObjectName(u"tab_custom_path")
        self.gridLayout_3 = QGridLayout(self.tab_custom_path)
        self.gridLayout_3.setSpacing(6)
        self.gridLayout_3.setContentsMargins(11, 11, 11, 11)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.custom_path_edit = QLineEdit(self.tab_custom_path)
        self.custom_path_edit.setObjectName(u"custom_path_edit")

        self.gridLayout_3.addWidget(self.custom_path_edit, 1, 0, 1, 1)

        self.custom_path_button = QPushButton(self.tab_custom_path)
        self.custom_path_button.setObjectName(u"custom_path_button")
        self.custom_path_button.setMaximumSize(QSize(100, 16777215))

        self.gridLayout_3.addWidget(self.custom_path_button, 1, 1, 1, 1)

        self.custom_path_label = QLabel(self.tab_custom_path)
        self.custom_path_label.setObjectName(u"custom_path_label")
        self.custom_path_label.setWordWrap(True)

        self.gridLayout_3.addWidget(self.custom_path_label, 0, 0, 1, 2)

        self.output_tab_widget.addTab(self.tab_custom_path, "")

        self.root_layout.addWidget(self.output_tab_widget, 10, 0, 2, 3)

        self.console_reminder_label = QLabel(MSRGameExportDialog)
        self.console_reminder_label.setObjectName(u"console_reminder_label")
        self.console_reminder_label.setWordWrap(True)

        self.root_layout.addWidget(self.console_reminder_label, 8, 0, 1, 3)

        self.line = QFrame(MSRGameExportDialog)
        self.line.setObjectName(u"line")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.line.sizePolicy().hasHeightForWidth())
        self.line.setSizePolicy(sizePolicy)
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.root_layout.addWidget(self.line, 4, 0, 1, 3)

        self.cancel_button = QPushButton(MSRGameExportDialog)
        self.cancel_button.setObjectName(u"cancel_button")

        self.root_layout.addWidget(self.cancel_button, 14, 2, 1, 1)

        self.encrypted_hint = QLabel(MSRGameExportDialog)
        self.encrypted_hint.setObjectName(u"encrypted_hint")

        self.root_layout.addWidget(self.encrypted_hint, 2, 0, 1, 3)

        self.auto_save_spoiler_check = QCheckBox(MSRGameExportDialog)
        self.auto_save_spoiler_check.setObjectName(u"auto_save_spoiler_check")

        self.root_layout.addWidget(self.auto_save_spoiler_check, 13, 0, 1, 1)


        self.retranslateUi(MSRGameExportDialog)

        self.output_tab_widget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MSRGameExportDialog)
    # setupUi

    def retranslateUi(self, MSRGameExportDialog):
        MSRGameExportDialog.setWindowTitle(QCoreApplication.translate("MSRGameExportDialog", u"Game Patching", None))
        self.input_file_label.setText(QCoreApplication.translate("MSRGameExportDialog", u"<html><head/><body><p>Input File (A decrypted 3ds, cci, cia, cxi or app Samus Returns rom file)</p></body></html>", None))
        self.input_file_button.setText(QCoreApplication.translate("MSRGameExportDialog", u"Select File", None))
        self.input_file_edit.setPlaceholderText(QCoreApplication.translate("MSRGameExportDialog", u"Path to vanilla rom file", None))
        self.accept_button.setText(QCoreApplication.translate("MSRGameExportDialog", u"Accept", None))
        self.target_platform_label.setText(QCoreApplication.translate("MSRGameExportDialog", u"Target Platform", None))
        self.luma_radio.setText(QCoreApplication.translate("MSRGameExportDialog", u"Luma3DS", None))
#if QT_CONFIG(tooltip)
        self.azahar_radio.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.azahar_radio.setText(QCoreApplication.translate("MSRGameExportDialog", u"Azahar", None))
        self.sd_label.setText(QCoreApplication.translate("MSRGameExportDialog", u"Select the drive letter for your SD Card", None))
        self.sd_combo.setItemText(0, QCoreApplication.translate("MSRGameExportDialog", u"D:", None))

        self.sd_non_removable.setText(QCoreApplication.translate("MSRGameExportDialog", u"Show non-removable", None))
        self.sd_refresh_button.setText(QCoreApplication.translate("MSRGameExportDialog", u"Refresh", None))
        self.output_tab_widget.setTabText(self.output_tab_widget.indexOf(self.tab_sd_card), QCoreApplication.translate("MSRGameExportDialog", u"SD Card", None))
        self.ftp_description_label.setText(QCoreApplication.translate("MSRGameExportDialog", u"<html><head/><body><p>Upload the exported mod directly to your 3DS, via FTP, to a path compatible with Luma3DS.</p><p>In order to provide a FTP server in your 3DS, you need to run ftpd. You can download it <a href=\"https://github.com/mtheall/ftpd/releases/latest\"><span style=\" text-decoration: underline; color:#007af4;\">here</span></a> or download it directly to your SD card with <a href=\"https://github.com/Universal-Team/Universal-Updater/releases/latest\"><span style=\" text-decoration: underline; color:#007af4;\">Universal Updater</span></a>.</p></body></html>", None))
        self.ftp_anonymous_check.setText(QCoreApplication.translate("MSRGameExportDialog", u"Anonymous", None))
        self.ftp_username_edit.setPlaceholderText(QCoreApplication.translate("MSRGameExportDialog", u"Username", None))
        self.ftp_password_edit.setPlaceholderText(QCoreApplication.translate("MSRGameExportDialog", u"Password", None))
        self.ftp_ip_label.setText(QCoreApplication.translate("MSRGameExportDialog", u"3DS IP", None))
        self.ftp_ip_edit.setInputMask("")
        self.ftp_ip_edit.setText("")
        self.ftp_ip_edit.setPlaceholderText(QCoreApplication.translate("MSRGameExportDialog", u"IP", None))
        self.ftp_port_edit.setText(QCoreApplication.translate("MSRGameExportDialog", u"21", None))
        self.ftp_port_edit.setPlaceholderText(QCoreApplication.translate("MSRGameExportDialog", u"Port", None))
        self.ftp_test_button.setText(QCoreApplication.translate("MSRGameExportDialog", u"Test connection", None))
        self.output_tab_widget.setTabText(self.output_tab_widget.indexOf(self.tab_ftp), QCoreApplication.translate("MSRGameExportDialog", u"Upload via FTP", None))
        self.azahar_label.setText(QCoreApplication.translate("MSRGameExportDialog", u"<html><head/><body><p>The game will be exported directly to Azahar's mod folder for Metroid: Samus Returns.</p><p>Path to be used:<br/><span style=\" font-size:8pt;\">{mod_path}</span></p><p>Please make sure Azahar is closed before exporting a game.</p></body></html>", None))
        self.output_tab_widget.setTabText(self.output_tab_widget.indexOf(self.tab_azahar), QCoreApplication.translate("MSRGameExportDialog", u"Azahar", None))
        self.custom_path_edit.setPlaceholderText(QCoreApplication.translate("MSRGameExportDialog", u"Path where to place randomized game", None))
        self.custom_path_button.setText(QCoreApplication.translate("MSRGameExportDialog", u"Select Folder", None))
        self.custom_path_label.setText(QCoreApplication.translate("MSRGameExportDialog", u"<html><head/><body><p>Saves the mod to a path or your choosing, leaving the responsibility of placing the files in the correct location to you.</p><p>This path and input path are not allowed to contain the other.</p><p>It's recommended to use one of the other options.</p></body></html>", None))
        self.output_tab_widget.setTabText(self.output_tab_widget.indexOf(self.tab_custom_path), QCoreApplication.translate("MSRGameExportDialog", u"Custom Path", None))
        self.console_reminder_label.setText(QCoreApplication.translate("MSRGameExportDialog", u"<html><head/><body><p>Ensure that Game Patching is enabled in Luma3DS first before launching the game.<br/>This can be done by holding SELECT when turning on your 3DS.</p></body></html>", None))
        self.cancel_button.setText(QCoreApplication.translate("MSRGameExportDialog", u"Cancel", None))
        self.encrypted_hint.setText(QCoreApplication.translate("MSRGameExportDialog", u"The rom file seems to be encrypted. Make sure to use a decrypted version!", None))
        self.auto_save_spoiler_check.setText(QCoreApplication.translate("MSRGameExportDialog", u"Include a spoiler log on same directory", None))
    # retranslateUi

