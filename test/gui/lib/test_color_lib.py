from randovania.gui.lib import color_lib


def test_hue_rotate_color():
    initial_color = (240, 128, 97)
    color = color_lib.hue_rotate_color(initial_color, 360)
    assert color == initial_color

    color_2 = color_lib.hue_rotate_color(initial_color, 380)
    color_3 = color_lib.hue_rotate_color(initial_color, 20)
    assert color_2 == color_3

    color_4 = color_lib.hue_rotate_color(initial_color, 0)
    assert color_4 == initial_color
