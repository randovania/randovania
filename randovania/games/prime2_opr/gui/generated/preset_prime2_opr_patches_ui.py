# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_prime2_opr_patches.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QFrame, QLabel,
    QMainWindow, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

class Ui_PresetEchoesOPRPatches(object):
    def setupUi(self, PresetEchoesOPRPatches):
        if not PresetEchoesOPRPatches.objectName():
            PresetEchoesOPRPatches.setObjectName(u"PresetEchoesOPRPatches")
        PresetEchoesOPRPatches.resize(466, 611)
        self.centralWidget = QWidget(PresetEchoesOPRPatches)
        self.centralWidget.setObjectName(u"centralWidget")
        self.centralWidget.setMaximumSize(QSize(16777215, 16777215))
        self.verticalLayout = QVBoxLayout(self.centralWidget)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(4, 4, 4, 4)
        self.include_practice_mod_check = QCheckBox(self.centralWidget)
        self.include_practice_mod_check.setObjectName(u"include_practice_mod_check")
        self.include_practice_mod_check.setEnabled(True)

        self.verticalLayout.addWidget(self.include_practice_mod_check)

        self.include_practice_mod_label = QLabel(self.centralWidget)
        self.include_practice_mod_label.setObjectName(u"include_practice_mod_label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.include_practice_mod_label.sizePolicy().hasHeightForWidth())
        self.include_practice_mod_label.setSizePolicy(sizePolicy)
        self.include_practice_mod_label.setMaximumSize(QSize(16777215, 60))
        self.include_practice_mod_label.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        self.include_practice_mod_label.setWordWrap(True)
        self.include_practice_mod_label.setOpenExternalLinks(True)

        self.verticalLayout.addWidget(self.include_practice_mod_label)

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

        self.portal_rando_line = QFrame(self.centralWidget)
        self.portal_rando_line.setObjectName(u"portal_rando_line")
        self.portal_rando_line.setFrameShape(QFrame.Shape.HLine)
        self.portal_rando_line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.portal_rando_line)

        self.portal_rando_check = QCheckBox(self.centralWidget)
        self.portal_rando_check.setObjectName(u"portal_rando_check")

        self.verticalLayout.addWidget(self.portal_rando_check)

        self.portal_rando_label = QLabel(self.centralWidget)
        self.portal_rando_label.setObjectName(u"portal_rando_label")
        self.portal_rando_label.setWordWrap(True)

        self.verticalLayout.addWidget(self.portal_rando_label)

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
        self.inverted_label.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        self.inverted_label.setWordWrap(True)

        self.verticalLayout.addWidget(self.inverted_label)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        PresetEchoesOPRPatches.setCentralWidget(self.centralWidget)

        self.retranslateUi(PresetEchoesOPRPatches)

        QMetaObject.connectSlotsByName(PresetEchoesOPRPatches)
    # setupUi

    def retranslateUi(self, PresetEchoesOPRPatches):
        PresetEchoesOPRPatches.setWindowTitle(QCoreApplication.translate("PresetEchoesOPRPatches", u"Other", None))
        self.include_practice_mod_check.setText(QCoreApplication.translate("PresetEchoesOPRPatches", u"Include Practice Mod", None))
        self.include_practice_mod_label.setText(QCoreApplication.translate("PresetEchoesOPRPatches", u"<html><head/><body><p>Practice Mod is a practice tool for Echoes, allowing in-game changes to which items you have and warping to all rooms.</p><p>See the <a href=\"https://github.com/MetroidPrimeModding/prime2-practice-mod/blob/main/README.md\"><span style=\" text-decoration: underline; color:#0000ff;\">Practice Mod README</span></a> for more details.</p></body></html>", None))
        self.save_doors_check.setText(QCoreApplication.translate("PresetEchoesOPRPatches", u"Force all Save Station doors to be unlocked", None))
        self.save_doors_label.setText(QCoreApplication.translate("PresetEchoesOPRPatches", u"This ensures you can easily access Save Stations, regardless of your inventory or of door lock randomization.", None))
        self.portal_rando_check.setText(QCoreApplication.translate("PresetEchoesOPRPatches", u"Portal Randomizer", None))
        self.portal_rando_label.setText(QCoreApplication.translate("PresetEchoesOPRPatches", u"<html><head/><body><p>This randomizes the connections between portals. Dark Portals will always go to Dark Aether in the same region, and Light Portals will always go to Light Aether in the same region.</p><p>When enabled, this setting also adds some new portals to existing portal destinations, to ensure that all portals are two-way.</p></body></html>", None))
        self.inverted_check.setText(QCoreApplication.translate("PresetEchoesOPRPatches", u"[Chaos] Inverted Aether", None))
        self.inverted_label.setText(QCoreApplication.translate("PresetEchoesOPRPatches", u"<html><head/><body><p>In this mode, it's the Light Aether atmosphere that is dangerous!<br/>All safe zones are moved to Light Aether, but that's not enough so it's still extremely dangerous.</p><p>Logic always acts as if this option is disabled.</p></body></html>", None))
    # retranslateUi

