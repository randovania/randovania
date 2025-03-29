from __future__ import annotations

import typing
from pathlib import Path

from PySide6 import QtWidgets


class MultiFormatOutputMixin:
    _selected_output_format: str
    _base_output_name: str
    output_format_layout: QtWidgets.QHBoxLayout
    output_file_edit: QtWidgets.QLineEdit
    format_radio_buttons: dict[str, QtWidgets.QRadioButton]

    @property
    def valid_output_file_types(self) -> list[str]:
        raise NotImplementedError

    @property
    def available_output_file_types(self) -> list[str]:
        return self.valid_output_file_types

    @property
    def default_output_name(self):
        return f"{self._base_output_name}.{self._selected_output_format}"

    def setup_multi_format(self, output_format: str | None):
        available_types = self.available_output_file_types

        if output_format is not None and output_format in available_types:
            self._selected_output_format = output_format
        else:
            self._selected_output_format = self.valid_output_file_types[0]

        self.format_radio_buttons = {}

        for filetype in self.valid_output_file_types:
            radio = QtWidgets.QRadioButton("." + filetype, typing.cast("QtWidgets.QWidget", self))
            if filetype == self._selected_output_format:
                radio.setChecked(True)
            radio.setEnabled(filetype in available_types)
            radio.toggled.connect(self._on_output_format_changed)
            self.format_radio_buttons[filetype] = radio
            self.output_format_layout.addWidget(radio)

    def _on_output_format_changed(self):
        button = typing.cast("QtWidgets.QWidget", self).sender()
        if button.isChecked():
            self._selected_output_format = button.text()[1:]
            current_filename = Path(self.output_file_edit.text())
            if str(current_filename) != ".":
                self.output_file_edit.setText(str(current_filename.with_suffix("." + self._selected_output_format)))
                self.output_file_edit.field_validation()
