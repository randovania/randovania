from __future__ import annotations

import math

import numpy
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


def hue_rotate_matrix(degrees: float) -> numpy.ndarray:
    """Luminance-preserving hue rotation matrix, mirroring randomprime's `huerotate_matrix`."""
    # Kept in float32 throughout, so the result is bit-for-bit what randomprime's f32 math produces.
    radians = numpy.float32(degrees) * numpy.float32(math.pi) / numpy.float32(180.0)
    cos_v = numpy.cos(radians)
    sin_v = numpy.sin(radians)
    return numpy.array(
        [
            [
                0.213 + cos_v * 0.787 - sin_v * 0.213,
                0.715 - cos_v * 0.715 - sin_v * 0.715,
                0.072 - cos_v * 0.072 + sin_v * 0.928,
            ],
            [
                0.213 - cos_v * 0.213 + sin_v * 0.143,
                0.715 + cos_v * 0.285 + sin_v * 0.140,
                0.072 - cos_v * 0.072 - sin_v * 0.283,
            ],
            [
                0.213 - cos_v * 0.213 - sin_v * 0.787,
                0.715 - cos_v * 0.715 + sin_v * 0.715,
                0.072 + cos_v * 0.928 + sin_v * 0.072,
            ],
        ],
        dtype=numpy.float32,
    )


def image_to_rgba_array(image: QtGui.QImage) -> numpy.ndarray:
    """Converts a QImage into a (height, width, 4) uint8 array that no longer aliases the image's memory."""
    rgba = image.convertToFormat(QtGui.QImage.Format.Format_RGBA8888)
    buffer = numpy.frombuffer(rgba.constBits(), dtype=numpy.uint8)
    return buffer.reshape(rgba.height(), rgba.width(), 4).copy()


def hue_rotate_rgba_array(rgba: numpy.ndarray, matrix: numpy.ndarray) -> QtGui.QImage:
    """Applies a `hue_rotate_matrix` to every pixel's color, leaving alpha untouched."""
    result = rgba.copy()
    red, green, blue = (rgba[..., channel].astype(numpy.float32) for channel in range(3))
    for channel, row in enumerate(matrix):
        rotated = row[0] * red + row[1] * green + row[2] * blue
        # randomprime casts f32 to u8 after clamping, which truncates rather than rounds.
        result[..., channel] = numpy.clip(rotated, 0.0, 255.0).astype(numpy.uint8)

    height, width, _ = result.shape
    image = QtGui.QImage(result.data, width, height, width * 4, QtGui.QImage.Format.Format_RGBA8888)
    # QImage wraps the buffer without owning it, so it has to be copied before `result` is collected.
    return image.copy()
