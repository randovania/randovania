from PySide6 import QtWidgets, QtCore, QtGui


class VerticalTabBar(QtWidgets.QTabBar):
    def tabSizeHint(self, index: int) -> QtCore.QSize:
        return super().tabSizeHint(index).transposed()

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        painter = QtWidgets.QStylePainter(self)
        opt = QtWidgets.QStyleOptionTab()

        for i in range(self.count()):
            self.initStyleOption(opt, i)
            painter.drawControl(QtWidgets.QStyle.CE_TabBarTabShape, opt)
            painter.save()

            s = opt.rect.size()
            s.transpose()
            r = QtCore.QRect(QtCore.QPoint(), s)
            r.moveCenter(opt.rect.center())
            opt.rect = r

            c = QtCore.QPoint(self.tabRect(i).center())
            painter.translate(c)
            painter.rotate(90)
            painter.translate(-c)
            painter.drawControl(QtWidgets.QStyle.CE_TabBarTabLabel, opt)
            painter.restore()
