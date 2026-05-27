# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_prime_hunters_hints.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QGroupBox, QLabel,
    QMainWindow, QScrollArea, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

class Ui_PresetHuntersHints(object):
    def setupUi(self, PresetHuntersHints):
        if not PresetHuntersHints.objectName():
            PresetHuntersHints.setObjectName(u"PresetHuntersHints")
        PresetHuntersHints.resize(595, 580)
        self.centralWidget = QWidget(PresetHuntersHints)
        self.centralWidget.setObjectName(u"centralWidget")
        self.centralWidget.setMaximumSize(QSize(16777215, 16777215))
        self.hint_layout = QVBoxLayout(self.centralWidget)
        self.hint_layout.setSpacing(6)
        self.hint_layout.setContentsMargins(11, 11, 11, 11)
        self.hint_layout.setObjectName(u"hint_layout")
        self.hint_layout.setContentsMargins(6, 6, 6, 6)
        self.scroll_area = QScrollArea(self.centralWidget)
        self.scroll_area.setObjectName(u"scroll_area")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area_contents = QWidget()
        self.scroll_area_contents.setObjectName(u"scroll_area_contents")
        self.scroll_area_contents.setGeometry(QRect(0, 0, 581, 566))
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scroll_area_contents.sizePolicy().hasHeightForWidth())
        self.scroll_area_contents.setSizePolicy(sizePolicy)
        self.scroll_area_layout = QVBoxLayout(self.scroll_area_contents)
        self.scroll_area_layout.setSpacing(6)
        self.scroll_area_layout.setContentsMargins(11, 11, 11, 11)
        self.scroll_area_layout.setObjectName(u"scroll_area_layout")
        self.scroll_area_layout.setContentsMargins(6, 6, 6, 6)
        self.hint_octolith_group = QGroupBox(self.scroll_area_contents)
        self.hint_octolith_group.setObjectName(u"hint_octolith_group")
        self.verticalLayout_2 = QVBoxLayout(self.hint_octolith_group)
        self.verticalLayout_2.setSpacing(6)
        self.verticalLayout_2.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.hint_octolith_label = QLabel(self.hint_octolith_group)
        self.hint_octolith_label.setObjectName(u"hint_octolith_label")
        self.hint_octolith_label.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.hint_octolith_label)

        self.hint_octolith_combo = QComboBox(self.hint_octolith_group)
        self.hint_octolith_combo.addItem("")
        self.hint_octolith_combo.addItem("")
        self.hint_octolith_combo.addItem("")
        self.hint_octolith_combo.setObjectName(u"hint_octolith_combo")

        self.verticalLayout_2.addWidget(self.hint_octolith_combo)


        self.scroll_area_layout.addWidget(self.hint_octolith_group)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.scroll_area_layout.addItem(self.verticalSpacer)

        self.scroll_area.setWidget(self.scroll_area_contents)

        self.hint_layout.addWidget(self.scroll_area)

        PresetHuntersHints.setCentralWidget(self.centralWidget)

        self.retranslateUi(PresetHuntersHints)

        QMetaObject.connectSlotsByName(PresetHuntersHints)
    # setupUi

    def retranslateUi(self, PresetHuntersHints):
        PresetHuntersHints.setWindowTitle(QCoreApplication.translate("PresetHuntersHints", u"Hints", None))
        self.hint_octolith_group.setTitle(QCoreApplication.translate("PresetHuntersHints", u"Octoliths", None))
        self.hint_octolith_label.setText(QCoreApplication.translate("PresetHuntersHints", u"<html><head/><body><p>This controls how precise the Octolith hints in Alimbic Cannon Control Room are.</p><p><span style=\" font-weight:600;\">No hints</span>: The hints provide no useful information.</p><p><span style=\" font-weight:600;\">Show only the area name</span>: Each hint says the area name for the corresponding Octolith (&quot;Celestial Archives&quot;, &quot;Arcterra&quot;, etc.)</p><p><span style=\" font-weight:600;\">Show area and room name</span>: Each scan says the area and room name for the corresponding Octolith (&quot;Celestial Archives - Biodefense Chamber A&quot;, &quot;Arcterra - Biodefense Chamber B&quot;, etc.).</p></body></html>", None))
        self.hint_octolith_combo.setItemText(0, QCoreApplication.translate("PresetHuntersHints", u"No hints", None))
        self.hint_octolith_combo.setItemText(1, QCoreApplication.translate("PresetHuntersHints", u"Show only the area name", None))
        self.hint_octolith_combo.setItemText(2, QCoreApplication.translate("PresetHuntersHints", u"Show area and room name", None))

    # retranslateUi

