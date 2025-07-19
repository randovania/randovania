# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'generate_game_widget.ui'
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
from PySide6.QtWidgets import (QApplication, QGridLayout, QPushButton, QSizePolicy,
    QSpinBox, QWidget)

from randovania.gui.widgets.select_preset_widget import SelectPresetWidget

class Ui_GenerateGameWidget(object):
    def setupUi(self, GenerateGameWidget):
        if not GenerateGameWidget.objectName():
            GenerateGameWidget.setObjectName(u"GenerateGameWidget")
        GenerateGameWidget.resize(409, 312)
        self.create_layout = QGridLayout(GenerateGameWidget)
        self.create_layout.setSpacing(6)
        self.create_layout.setContentsMargins(11, 11, 11, 11)
        self.create_layout.setObjectName(u"create_layout")
        self.create_layout.setContentsMargins(4, 4, 4, 0)
        self.create_generate_no_retry_button = QPushButton(GenerateGameWidget)
        self.create_generate_no_retry_button.setObjectName(u"create_generate_no_retry_button")

        self.create_layout.addWidget(self.create_generate_no_retry_button, 3, 0, 1, 1)

        self.create_generate_button = QPushButton(GenerateGameWidget)
        self.create_generate_button.setObjectName(u"create_generate_button")

        self.create_layout.addWidget(self.create_generate_button, 3, 1, 1, 1)

        self.num_worlds_spin_box = QSpinBox(GenerateGameWidget)
        self.num_worlds_spin_box.setObjectName(u"num_worlds_spin_box")
        self.num_worlds_spin_box.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        self.num_worlds_spin_box.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.num_worlds_spin_box.setMinimum(1)

        self.create_layout.addWidget(self.num_worlds_spin_box, 3, 3, 1, 1)

        self.create_generate_race_button = QPushButton(GenerateGameWidget)
        self.create_generate_race_button.setObjectName(u"create_generate_race_button")

        self.create_layout.addWidget(self.create_generate_race_button, 3, 2, 1, 1)

        self.select_preset_widget = SelectPresetWidget(GenerateGameWidget)
        self.select_preset_widget.setObjectName(u"select_preset_widget")

        self.create_layout.addWidget(self.select_preset_widget, 2, 0, 1, 4)


        self.retranslateUi(GenerateGameWidget)

        QMetaObject.connectSlotsByName(GenerateGameWidget)
    # setupUi

    def retranslateUi(self, GenerateGameWidget):
        self.create_generate_no_retry_button.setText(QCoreApplication.translate("GenerateGameWidget", u"Generate without retry", None))
        self.create_generate_button.setText(QCoreApplication.translate("GenerateGameWidget", u"Generate", None))
        self.num_worlds_spin_box.setSuffix(QCoreApplication.translate("GenerateGameWidget", u" worlds", None))
        self.create_generate_race_button.setText(QCoreApplication.translate("GenerateGameWidget", u"Generate for Race", None))
        pass
    # retranslateUi

