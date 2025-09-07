# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_echoes_patches.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QFrame, QLabel,
    QMainWindow, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

class Ui_PresetEchoesPatches(object):
    def setupUi(self, PresetEchoesPatches):
        if not PresetEchoesPatches.objectName():
            PresetEchoesPatches.setObjectName(u"PresetEchoesPatches")
        PresetEchoesPatches.resize(466, 552)
        self.centralWidget = QWidget(PresetEchoesPatches)
        self.centralWidget.setObjectName(u"centralWidget")
        self.centralWidget.setMaximumSize(QSize(16777215, 16777215))
        self.verticalLayout = QVBoxLayout(self.centralWidget)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(4, 4, 4, 4)
        self.include_menu_mod_check = QCheckBox(self.centralWidget)
        self.include_menu_mod_check.setObjectName(u"include_menu_mod_check")
        self.include_menu_mod_check.setEnabled(True)

        self.verticalLayout.addWidget(self.include_menu_mod_check)

        self.include_menu_mod_label = QLabel(self.centralWidget)
        self.include_menu_mod_label.setObjectName(u"include_menu_mod_label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.include_menu_mod_label.sizePolicy().hasHeightForWidth())
        self.include_menu_mod_label.setSizePolicy(sizePolicy)
        self.include_menu_mod_label.setMaximumSize(QSize(16777215, 60))
        self.include_menu_mod_label.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.include_menu_mod_label.setWordWrap(True)
        self.include_menu_mod_label.setOpenExternalLinks(True)

        self.verticalLayout.addWidget(self.include_menu_mod_label)

        self.warp_to_start_line = QFrame(self.centralWidget)
        self.warp_to_start_line.setObjectName(u"warp_to_start_line")
        self.warp_to_start_line.setFrameShape(QFrame.Shape.HLine)
        self.warp_to_start_line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.warp_to_start_line)

        self.warp_to_start_check = QCheckBox(self.centralWidget)
        self.warp_to_start_check.setObjectName(u"warp_to_start_check")

        self.verticalLayout.addWidget(self.warp_to_start_check)

        self.warp_to_start_label = QLabel(self.centralWidget)
        self.warp_to_start_label.setObjectName(u"warp_to_start_label")
        sizePolicy.setHeightForWidth(self.warp_to_start_label.sizePolicy().hasHeightForWidth())
        self.warp_to_start_label.setSizePolicy(sizePolicy)
        self.warp_to_start_label.setMaximumSize(QSize(16777215, 70))
        self.warp_to_start_label.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.warp_to_start_label.setWordWrap(True)

        self.verticalLayout.addWidget(self.warp_to_start_label)

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

        self.new_patcher_line = QFrame(self.centralWidget)
        self.new_patcher_line.setObjectName(u"new_patcher_line")
        self.new_patcher_line.setFrameShape(QFrame.Shape.HLine)
        self.new_patcher_line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.new_patcher_line)

        self.new_patcher_check = QCheckBox(self.centralWidget)
        self.new_patcher_check.setObjectName(u"new_patcher_check")

        self.verticalLayout.addWidget(self.new_patcher_check)

        self.new_patcher_label = QLabel(self.centralWidget)
        self.new_patcher_label.setObjectName(u"new_patcher_label")
        self.new_patcher_label.setAlignment(Qt.AlignJustify|Qt.AlignTop)
        self.new_patcher_label.setWordWrap(True)

        self.verticalLayout.addWidget(self.new_patcher_label)

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
        self.include_menu_mod_check.setText(QCoreApplication.translate("PresetEchoesPatches", u"Include Menu Mod", None))
        self.include_menu_mod_label.setText(QCoreApplication.translate("PresetEchoesPatches", u"<html><head/><body><p>Menu Mod is a practice tool for Echoes, allowing in-game changes to which items you have and warping to all rooms.</p><p>See the <a href=\"https://www.dropbox.com/s/yhqqafaxfo3l4vn/Echoes%20Menu.7z?file_subpath=%2FEchoes+Menu%2Freadme.txt\"><span style=\" text-decoration: underline; color:#0000ff;\">Menu Mod README</span></a> for more details.</p></body></html>", None))
        self.warp_to_start_check.setText(QCoreApplication.translate("PresetEchoesPatches", u"Add warping to starting location from save stations", None))
        self.warp_to_start_label.setText(QCoreApplication.translate("PresetEchoesPatches", u"<html><head/><body><p>Refusing to save at any Save Station will prompt if you want to warp to the starting location (by default, Samus' ship in Landing Site).</p><p><span style=\" color:#005500;\">Usage of the this option is encouraged for all, as it prevents many softlocks that occurs normally in Echoes.</span></p></body></html>", None))
        self.save_doors_check.setText(QCoreApplication.translate("PresetEchoesPatches", u"Force all Save Station doors to be unlocked", None))
        self.save_doors_label.setText(QCoreApplication.translate("PresetEchoesPatches", u"This ensures you can easily access Save Stations, regardless of your inventory or of door lock randomization.", None))
        self.new_patcher_check.setText(QCoreApplication.translate("PresetEchoesPatches", u"[Experimental] Use new patcher", None))
        self.new_patcher_label.setText(QCoreApplication.translate("PresetEchoesPatches", u"<html><head/><body><p>Activates the use of the new patcher in addition to the existing one.</p><p>With this enabled:<br/>- Certain in-game puzzles will have their solution randomized, but are also modified to have better accessibility.<br/>- Dynamo Chamber and Trooper Security Station now start in post-layer change state</p><p>It's also required for certain new features, such as Inverted Aether.</p><p>This setting causes additional stuttering during gameplay, especially on Dolphin. It's recommended to unlock disc read speeds.</p></body></html>", None))
        self.portal_rando_check.setText(QCoreApplication.translate("PresetEchoesPatches", u"[Experimental] Portal Randomizer", None))
        self.portal_rando_label.setText(QCoreApplication.translate("PresetEchoesPatches", u"<html><head/><body><p>Randomizes portals inside each region. Requires the new patcher to be enabled.</p></body></html>", None))
        self.inverted_check.setText(QCoreApplication.translate("PresetEchoesPatches", u"[Unsupported] Inverted Aether", None))
        self.inverted_label.setText(QCoreApplication.translate("PresetEchoesPatches", u"<html><head/><body><p>In this mode, it's the Light Aether atmosphere that is dangerous!<br/>All safe zones are moved to Light Aether, but that's not enough so it's still extremely dangerous.</p><p>Logic always acts as if this option is disabled.</p></body></html>", None))
    # retranslateUi

