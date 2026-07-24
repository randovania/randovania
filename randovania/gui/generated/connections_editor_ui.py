# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'connections_editor.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QComboBox, QDialog,
    QDialogButtonBox, QFrame, QHBoxLayout, QHeaderView,
    QLabel, QLayout, QPushButton, QSizePolicy,
    QSpacerItem, QStackedWidget, QTreeView, QVBoxLayout,
    QWidget)

class Ui_ConnectionEditor(object):
    def setupUi(self, ConnectionEditor):
        if not ConnectionEditor.objectName():
            ConnectionEditor.setObjectName(u"ConnectionEditor")
        ConnectionEditor.resize(600, 450)
        ConnectionEditor.setMinimumSize(QSize(600, 300))
        ConnectionEditor.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.verticalLayout = QVBoxLayout(ConnectionEditor)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.setSpacing(6)
        self.buttons_layout.setObjectName(u"buttons_layout")
        self.buttons_layout.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)
        self.button_add_requirement = QPushButton(ConnectionEditor)
        self.button_add_requirement.setObjectName(u"button_add_requirement")

        self.buttons_layout.addWidget(self.button_add_requirement)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.buttons_layout.addItem(self.horizontalSpacer)

        self.button_shift_up = QPushButton(ConnectionEditor)
        self.button_shift_up.setObjectName(u"button_shift_up")
        self.button_shift_up.setMinimumSize(QSize(40, 0))

        self.buttons_layout.addWidget(self.button_shift_up)

        self.button_shift_down = QPushButton(ConnectionEditor)
        self.button_shift_down.setObjectName(u"button_shift_down")
        self.button_shift_down.setMinimumSize(QSize(40, 0))

        self.buttons_layout.addWidget(self.button_shift_down)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.buttons_layout.addItem(self.horizontalSpacer_2)

        self.button_delete = QPushButton(ConnectionEditor)
        self.button_delete.setObjectName(u"button_delete")

        self.buttons_layout.addWidget(self.button_delete)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.buttons_layout.addItem(self.horizontalSpacer_3)

        self.button_undo = QPushButton(ConnectionEditor)
        self.button_undo.setObjectName(u"button_undo")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.button_undo.sizePolicy().hasHeightForWidth())
        self.button_undo.setSizePolicy(sizePolicy)
        self.button_undo.setMinimumSize(QSize(40, 0))

        self.buttons_layout.addWidget(self.button_undo)

        self.button_redo = QPushButton(ConnectionEditor)
        self.button_redo.setObjectName(u"button_redo")
        self.button_redo.setMinimumSize(QSize(40, 0))

        self.buttons_layout.addWidget(self.button_redo)

        self.horizontalSpacer_5 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.buttons_layout.addItem(self.horizontalSpacer_5)

        self.buttons_layout.setStretch(0, 5)
        self.buttons_layout.setStretch(1, 1)
        self.buttons_layout.setStretch(2, 2)
        self.buttons_layout.setStretch(3, 2)
        self.buttons_layout.setStretch(4, 1)
        self.buttons_layout.setStretch(5, 3)
        self.buttons_layout.setStretch(6, 1)
        self.buttons_layout.setStretch(7, 2)
        self.buttons_layout.setStretch(8, 2)

        self.verticalLayout.addLayout(self.buttons_layout)

        self.tree_view = QTreeView(ConnectionEditor)
        self.tree_view.setObjectName(u"tree_view")

        self.verticalLayout.addWidget(self.tree_view)

        self.editors_control_layout = QHBoxLayout()
        self.editors_control_layout.setObjectName(u"editors_control_layout")
        self.label = QLabel(ConnectionEditor)
        self.label.setObjectName(u"label")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy1)

        self.editors_control_layout.addWidget(self.label)

        self.combo_requirement_type = QComboBox(ConnectionEditor)
        self.combo_requirement_type.setObjectName(u"combo_requirement_type")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.combo_requirement_type.sizePolicy().hasHeightForWidth())
        self.combo_requirement_type.setSizePolicy(sizePolicy2)

        self.editors_control_layout.addWidget(self.combo_requirement_type)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.editors_control_layout.addItem(self.horizontalSpacer_4)

        self.editors_control_layout.setStretch(0, 1)

        self.verticalLayout.addLayout(self.editors_control_layout)

        self.line = QFrame(ConnectionEditor)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.line)

        self.stacked_widget = QStackedWidget(ConnectionEditor)
        self.stacked_widget.setObjectName(u"stacked_widget")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.stacked_widget.sizePolicy().hasHeightForWidth())
        self.stacked_widget.setSizePolicy(sizePolicy3)
        self.page = QWidget()
        self.page.setObjectName(u"page")
        self.stacked_widget.addWidget(self.page)
        self.page_2 = QWidget()
        self.page_2.setObjectName(u"page_2")
        self.stacked_widget.addWidget(self.page_2)

        self.verticalLayout.addWidget(self.stacked_widget)

        self.button_box = QDialogButtonBox(ConnectionEditor)
        self.button_box.setObjectName(u"button_box")
        self.button_box.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok)
        self.button_box.setCenterButtons(False)

        self.verticalLayout.addWidget(self.button_box)

        QWidget.setTabOrder(self.button_add_requirement, self.button_shift_up)
        QWidget.setTabOrder(self.button_shift_up, self.button_shift_down)
        QWidget.setTabOrder(self.button_shift_down, self.button_delete)
        QWidget.setTabOrder(self.button_delete, self.tree_view)
        QWidget.setTabOrder(self.tree_view, self.combo_requirement_type)

        self.retranslateUi(ConnectionEditor)
        self.button_box.accepted.connect(ConnectionEditor.accept)
        self.button_box.rejected.connect(ConnectionEditor.reject)

        QMetaObject.connectSlotsByName(ConnectionEditor)
    # setupUi

    def retranslateUi(self, ConnectionEditor):
        ConnectionEditor.setWindowTitle(QCoreApplication.translate("ConnectionEditor", u"Connection Editor", None))
        self.button_add_requirement.setText(QCoreApplication.translate("ConnectionEditor", u"\uff0b Requirement", None))
        self.button_shift_up.setText(QCoreApplication.translate("ConnectionEditor", u"\u25b2", None))
        self.button_shift_down.setText(QCoreApplication.translate("ConnectionEditor", u"\u25bc", None))
        self.button_delete.setText(QCoreApplication.translate("ConnectionEditor", u"Delete", None))
        self.button_undo.setText(QCoreApplication.translate("ConnectionEditor", u"Undo", None))
        self.button_redo.setText(QCoreApplication.translate("ConnectionEditor", u"Redo", None))
        self.label.setText(QCoreApplication.translate("ConnectionEditor", u"Type:", None))
    # retranslateUi

