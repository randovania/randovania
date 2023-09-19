from collections.abc import Callable

from PySide6 import QtWidgets


def create_label_slider_updater(
    label: QtWidgets.QLabel,
    display_as_percentage: bool,
) -> Callable[[QtWidgets.QSlider], None]:
    """Given a label, creates a function that takes a slider and updates the label with the value.
    :param label: The label to bind.
    :param display_as_percentage: Converts the slider value into a percentage."""
    if display_as_percentage:

        def _update(slider: QtWidgets.QSlider) -> None:
            min_value = slider.minimum()
            percentage = (slider.value() - min_value) / (slider.maximum() - min_value)
            label.setText(f"{percentage * 100: 3.0f}%")

    else:

        def _update(slider: QtWidgets.QSlider) -> None:
            label.setText(str(slider.value()))

    return _update
