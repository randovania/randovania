from __future__ import annotations

import numpy
import pytest

from randovania.gui.lib import color_lib

# Produced by randomprime's `huerotate_in_place`, which this module must reproduce exactly.
RANDOMPRIME_REFERENCE = {
    0: [(255, 173, 50, 255), (220, 25, 45, 128), (0, 0, 0, 255), (255, 255, 255, 0), (40, 20, 90, 200)],
    37: [(161, 202, 32, 255), (175, 47, 0, 128), (0, 0, 0, 255), (255, 255, 254, 0), (74, 11, 71, 200)],
    90: [(50, 228, 108, 255), (44, 90, 0, 128), (0, 0, 0, 255), (255, 255, 255, 0), (90, 12, 18, 200)],
    180: [(108, 190, 255, 255), (0, 110, 90, 128), (0, 0, 0, 255), (255, 255, 254, 0), (18, 38, 0, 200)],
    275: [(255, 134, 243, 255), (104, 42, 217, 128), (0, 0, 0, 255), (254, 255, 255, 0), (0, 45, 45, 200)],
    360: [(254, 173, 49, 255), (219, 25, 44, 128), (0, 0, 0, 255), (255, 254, 255, 0), (40, 19, 90, 200)],
}


def test_hue_rotate_color():
    initial_color = (240, 128, 97)
    color = color_lib.hue_rotate_color(initial_color, 360)
    assert color == initial_color

    color_2 = color_lib.hue_rotate_color(initial_color, 380)
    color_3 = color_lib.hue_rotate_color(initial_color, 20)
    assert color_2 == color_3

    color_4 = color_lib.hue_rotate_color(initial_color, 0)
    assert color_4 == initial_color


@pytest.mark.parametrize("degrees", sorted(RANDOMPRIME_REFERENCE))
def test_hue_rotate_rgba_array_matches_randomprime(skip_qtbot, degrees: int) -> None:
    original = numpy.array([RANDOMPRIME_REFERENCE[0]], dtype=numpy.uint8)

    result = color_lib.hue_rotate_rgba_array(original, color_lib.hue_rotate_matrix(degrees))

    pixels = [tuple(int(value) for value in pixel) for pixel in color_lib.image_to_rgba_array(result)[0]]
    assert pixels == RANDOMPRIME_REFERENCE[degrees]
