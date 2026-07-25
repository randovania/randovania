# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_prime_hunters_extra_locations.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QLabel, QMainWindow,
    QSizePolicy, QVBoxLayout, QWidget)

class Ui_PresetHuntersExtraLocations(object):
    def setupUi(self, PresetHuntersExtraLocations):
        if not PresetHuntersExtraLocations.objectName():
            PresetHuntersExtraLocations.setObjectName(u"PresetHuntersExtraLocations")
        PresetHuntersExtraLocations.resize(768, 661)
        self.centralWidget = QWidget(PresetHuntersExtraLocations)
        self.centralWidget.setObjectName(u"centralWidget")
        self.centralWidget.setMaximumSize(QSize(16777215, 16777215))
        self.verticalLayout = QVBoxLayout(self.centralWidget)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.shuffle_item_refills_check_box = QCheckBox(self.centralWidget)
        self.shuffle_item_refills_check_box.setObjectName(u"shuffle_item_refills_check_box")

        self.verticalLayout.addWidget(self.shuffle_item_refills_check_box)

        self.shuffle_item_refills_label = QLabel(self.centralWidget)
        self.shuffle_item_refills_label.setObjectName(u"shuffle_item_refills_label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.shuffle_item_refills_label.sizePolicy().hasHeightForWidth())
        self.shuffle_item_refills_label.setSizePolicy(sizePolicy)
        self.shuffle_item_refills_label.setScaledContents(False)
        self.shuffle_item_refills_label.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.shuffle_item_refills_label.setWordWrap(True)

        self.verticalLayout.addWidget(self.shuffle_item_refills_label)

        self.shuffle_shield_keys_check_box = QCheckBox(self.centralWidget)
        self.shuffle_shield_keys_check_box.setObjectName(u"shuffle_shield_keys_check_box")

        self.verticalLayout.addWidget(self.shuffle_shield_keys_check_box)

        self.shuffle_shield_keys_label = QLabel(self.centralWidget)
        self.shuffle_shield_keys_label.setObjectName(u"shuffle_shield_keys_label")
        self.shuffle_shield_keys_label.setWordWrap(True)

        self.verticalLayout.addWidget(self.shuffle_shield_keys_label)

        PresetHuntersExtraLocations.setCentralWidget(self.centralWidget)

        self.retranslateUi(PresetHuntersExtraLocations)

        QMetaObject.connectSlotsByName(PresetHuntersExtraLocations)
    # setupUi

    def retranslateUi(self, PresetHuntersExtraLocations):
        PresetHuntersExtraLocations.setWindowTitle(QCoreApplication.translate("PresetHuntersExtraLocations", u"Goal", None))
        self.shuffle_item_refills_check_box.setText(QCoreApplication.translate("PresetHuntersExtraLocations", u"Shuffle Item Refill Locations", None))
        self.shuffle_item_refills_label.setText(QCoreApplication.translate("PresetHuntersExtraLocations", u"<html><head/><body><p>Shuffles locations where an Energy, Missile, or Universal Ammo refill is located. This will add an additional 30 locations to the pickup pool.</p><p><span style=\" font-weight:600;\">Number of Locations</span>:</p><ul style=\"margin-top: 0px; margin-bottom: 0px; margin-left: 0px; margin-right: 0px; -qt-list-indent: 1;\"><li style=\" margin-top:12px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Small Energy: 17</li><li style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Medium Energy: 7 (excludes 19 locations from Alinos - Magma Pool)</li><li style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Large Energy: 4</li><li style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Small Missile Pack: 1 (excludes 1 location to prevent softlocking)</li><li style="
                        "\" margin-top:0px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Large UA Pack: 1 (excludes 2 locations to prevent softlocking)</li></ul></body></html>", None))
        self.shuffle_shield_keys_check_box.setText(QCoreApplication.translate("PresetHuntersExtraLocations", u"Shuffle Shield Key Locations", None))
        self.shuffle_shield_keys_label.setText(QCoreApplication.translate("PresetHuntersExtraLocations", u"<html><head/><body><p>Shuffles locations where a Shield Key is located. Shield Keys are responsible for unlocking doors, Artifact Shields, and Force Fields. This will add an additional 24 locations to the pickup pool.</p><p><span style=\" font-weight:600;\">Shield Key Locations</span>:</p><p><span style=\" font-weight:600;\">Alinos</span></p><ul style=\"margin-top: 0px; margin-bottom: 0px; margin-left: 0px; margin-right: 0px; -qt-list-indent: 1;\"><li style=\" margin-top:12px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Echo Hall</li><li style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Elder Passage</li><li style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">High Ground</li><li style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Crash Site</li><li style=\" margin-t"
                        "op:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Council Chamber</li><li style=\" margin-top:0px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Piston Cave</li></ul><p><span style=\" font-weight:600;\">Celestial Archives</span></p><ul style=\"margin-top: 0px; margin-bottom: 0px; margin-left: 0px; margin-right: 0px; -qt-list-indent: 1;\"><li style=\" margin-top:12px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Data Shrine 01</li><li style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Data Shrine 03</li><li style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Synergy Core</li><li style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Docking Bay</li><li style=\" margin-top:0p"
                        "x; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Incubation Vault 01</li><li style=\" margin-top:0px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">New Arrival Registration</li></ul><p><span style=\" font-weight:600;\">Vesper Defense Outpost</span></p><ul style=\"margin-top: 0px; margin-bottom: 0px; margin-left: 0px; margin-right: 0px; -qt-list-indent: 1;\"><li style=\" margin-top:12px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Weapons Complex</li><li style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Compression Chamber x2</li><li style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Stasis Bunker x2</li><li style=\" margin-top:0px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Fuel Stack</"
                        "li></ul><p><span style=\" font-weight:600;\">Arcterra</span></p><ul style=\"margin-top: 0px; margin-bottom: 0px; margin-left: 0px; margin-right: 0px; -qt-list-indent: 1;\"><li style=\" margin-top:12px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Sic Transit</li><li style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Ice Hive</li><li style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Frost Labyrinth</li><li style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Sanctorus</li><li style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Fault Line</li><li style=\" margin-top:0px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Subterranean</li></ul></body></html>", None))
    # retranslateUi

