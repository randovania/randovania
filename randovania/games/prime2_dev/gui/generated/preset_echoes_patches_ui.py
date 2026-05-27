# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_echoes_patches.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFrame,
    QHBoxLayout, QLabel, QMainWindow, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)

class Ui_PresetEchoesPatches(object):
    def setupUi(self, PresetEchoesPatches):
        if not PresetEchoesPatches.objectName():
            PresetEchoesPatches.setObjectName(u"PresetEchoesPatches")
        PresetEchoesPatches.resize(466, 611)
        self.centralWidget = QWidget(PresetEchoesPatches)
        self.centralWidget.setObjectName(u"centralWidget")
        self.centralWidget.setMaximumSize(QSize(16777215, 16777215))
        self.verticalLayout = QVBoxLayout(self.centralWidget)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(4, 4, 4, 4)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.practice_mod_mode_label = QLabel(self.centralWidget)
        self.practice_mod_mode_label.setObjectName(u"practice_mod_mode_label")

        self.horizontalLayout.addWidget(self.practice_mod_mode_label)

        self.practice_mod_mode_combo = QComboBox(self.centralWidget)
        self.practice_mod_mode_combo.setObjectName(u"practice_mod_mode_combo")

        self.horizontalLayout.addWidget(self.practice_mod_mode_combo)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.practice_mod_description_label = QLabel(self.centralWidget)
        self.practice_mod_description_label.setObjectName(u"practice_mod_description_label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.practice_mod_description_label.sizePolicy().hasHeightForWidth())
        self.practice_mod_description_label.setSizePolicy(sizePolicy)
        self.practice_mod_description_label.setMaximumSize(QSize(16777215, 60))
        self.practice_mod_description_label.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.practice_mod_description_label.setWordWrap(True)
        self.practice_mod_description_label.setOpenExternalLinks(True)

        self.verticalLayout.addWidget(self.practice_mod_description_label)

        self.save_doors_line = QFrame(self.centralWidget)
        self.save_doors_line.setObjectName(u"save_doors_line")
        self.save_doors_line.setFrameShape(QFrame.Shape.HLine)
        self.save_doors_line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.save_doors_line)

        self.save_doors_check = QCheckBox(self.centralWidget)
        self.save_doors_check.setObjectName(u"save_doors_check")

        self.verticalLayout.addWidget(self.save_doors_check)

        self.save_doors_label = QLabel(self.centralWidget)
        self.save_doors_label.setObjectName(u"save_doors_label")
        self.save_doors_label.setWordWrap(True)

        self.verticalLayout.addWidget(self.save_doors_label)

        self.inverted_line = QFrame(self.centralWidget)
        self.inverted_line.setObjectName(u"inverted_line")
        self.inverted_line.setFrameShape(QFrame.Shape.HLine)
        self.inverted_line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.inverted_line)

        self.inverted_check = QCheckBox(self.centralWidget)
        self.inverted_check.setObjectName(u"inverted_check")

        self.verticalLayout.addWidget(self.inverted_check)

        self.inverted_label = QLabel(self.centralWidget)
        self.inverted_label.setObjectName(u"inverted_label")
        self.inverted_label.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.inverted_label.setWordWrap(True)

        self.verticalLayout.addWidget(self.inverted_label)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        PresetEchoesPatches.setCentralWidget(self.centralWidget)

        self.retranslateUi(PresetEchoesPatches)

        QMetaObject.connectSlotsByName(PresetEchoesPatches)
    # setupUi

    def retranslateUi(self, PresetEchoesPatches):
        PresetEchoesPatches.setWindowTitle(QCoreApplication.translate("PresetEchoesPatches", u"Other", None))
        self.practice_mod_mode_label.setText(QCoreApplication.translate("PresetEchoesPatches", u"Practice Mod Mode", None))
        self.practice_mod_description_label.setText(QCoreApplication.translate("PresetEchoesPatches", u"<html><head/><body><p>Practice Mod is a practice tool for Echoes, allowing in-game changes to which items you have and warping to all rooms.</p><p>See the <a href=\"https://github.com/MetroidPrimeModding/prime2-practice-mod/blob/main/README.md\"><span style=\" text-decoration: underline; color:#0000ff;\">Practice Mod README</span></a> for more details.</p></body></html>", None))
        self.save_doors_check.setText(QCoreApplication.translate("PresetEchoesPatches", u"Force all Save Station doors to be unlocked", None))
        self.save_doors_label.setText(QCoreApplication.translate("PresetEchoesPatches", u"This ensures you can easily access Save Stations, regardless of your inventory or of door lock randomization.", None))
        self.inverted_check.setText(QCoreApplication.translate("PresetEchoesPatches", u"[Unsupported] Inverted Aether", None))
        self.inverted_label.setText(QCoreApplication.translate("PresetEchoesPatches", u"<html><head/><body><p>In this mode, it's the Light Aether atmosphere that is dangerous!<br/>All safe zones are moved to Light Aether, but that's not enough so it's still extremely dangerous.</p><p>Logic always acts as if this option is disabled.</p></body></html>", None))
    # retranslateUi

