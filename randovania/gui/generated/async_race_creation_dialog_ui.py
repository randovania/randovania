# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'async_race_creation_dialog.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialog, QDialogButtonBox,
    QGroupBox, QHBoxLayout, QLabel, QProgressBar,
    QPushButton, QSizePolicy, QVBoxLayout, QWidget)

from randovania.gui.widgets.async_race_room_settings_widget import AsyncRaceRoomSettingsWidget
from randovania.gui.widgets.background_task_widget import BackgroundTaskWidget

class Ui_AsyncRaceCreationDialog(object):
    def setupUi(self, AsyncRaceCreationDialog):
        if not AsyncRaceCreationDialog.objectName():
            AsyncRaceCreationDialog.setObjectName(u"AsyncRaceCreationDialog")
        AsyncRaceCreationDialog.resize(431, 198)
        self.root_layout = QVBoxLayout(AsyncRaceCreationDialog)
        self.root_layout.setSpacing(6)
        self.root_layout.setContentsMargins(11, 11, 11, 11)
        self.root_layout.setObjectName(u"root_layout")
        self.settings_widget = AsyncRaceRoomSettingsWidget(AsyncRaceCreationDialog)
        self.settings_widget.setObjectName(u"settings_widget")

        self.root_layout.addWidget(self.settings_widget)

        self.preset_group = QGroupBox(AsyncRaceCreationDialog)
        self.preset_group.setObjectName(u"preset_group")
        self.horizontalLayout = QHBoxLayout(self.preset_group)
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setContentsMargins(11, 11, 11, 11)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.preset_label = QLabel(self.preset_group)
        self.preset_label.setObjectName(u"preset_label")

        self.horizontalLayout.addWidget(self.preset_label)

        self.preset_button = QPushButton(self.preset_group)
        self.preset_button.setObjectName(u"preset_button")

        self.horizontalLayout.addWidget(self.preset_button)


        self.root_layout.addWidget(self.preset_group)

        self.progress_label = QLabel(AsyncRaceCreationDialog)
        self.progress_label.setObjectName(u"progress_label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.progress_label.sizePolicy().hasHeightForWidth())
        self.progress_label.setSizePolicy(sizePolicy)
        self.progress_label.setTextFormat(Qt.TextFormat.MarkdownText)
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.progress_label.setWordWrap(True)
        self.progress_label.setOpenExternalLinks(True)

        self.root_layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar(AsyncRaceCreationDialog)
        self.progress_bar.setObjectName(u"progress_bar")
        self.progress_bar.setValue(0)
        self.progress_bar.setInvertedAppearance(False)

        self.root_layout.addWidget(self.progress_bar)

        self.button_box = QDialogButtonBox(AsyncRaceCreationDialog)
        self.button_box.setObjectName(u"button_box")
        self.button_box.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok)

        self.root_layout.addWidget(self.button_box)


        self.retranslateUi(AsyncRaceCreationDialog)

        QMetaObject.connectSlotsByName(AsyncRaceCreationDialog)
    # setupUi

    def retranslateUi(self, AsyncRaceCreationDialog):
        AsyncRaceCreationDialog.setWindowTitle(QCoreApplication.translate("AsyncRaceCreationDialog", u"Async Race Room Creation", None))
        self.preset_group.setTitle(QCoreApplication.translate("AsyncRaceCreationDialog", u"Preset", None))
        self.preset_label.setText(QCoreApplication.translate("AsyncRaceCreationDialog", u"No Preset Selected", None))
        self.preset_button.setText(QCoreApplication.translate("AsyncRaceCreationDialog", u"Select Preset", None))
        self.progress_label.setText("")
    # retranslateUi

