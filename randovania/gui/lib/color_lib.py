from PySide6 import QtGui


def hue_rotate_color(original_color: tuple[int, int, int], rotation: int) -> tuple[int, int, int]:
    color = QtGui.QColor.fromRgb(*original_color)
    h = color.hue() + rotation
    s = color.saturation()
    v = color.value()
    while h >= 360:
        h -= 360
    while h < 0:
        h += 360

    rotated_color = QtGui.QColor.fromHsv(h, s, v)
    return rotated_color.red(), rotated_color.green(), rotated_color.blue()
