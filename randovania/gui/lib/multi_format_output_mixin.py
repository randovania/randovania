import typing
from pathlib import Path
from typing import Optional

from PySide2 import QtWidgets


class MultiFormatOutputMixin:
    _selected_output_format: str
    output_format_layout: QtWidgets.QHBoxLayout
    output_file_edit: QtWidgets.QLineEdit

    @property
    def valid_output_file_types(self) -> list[str]:
        raise NotImplementedError()

    def _validate_output_file(self):
        raise NotImplementedError()

    def setup_multi_format(self, output_format: Optional[str]):
        self.output_file_edit.textChanged.connect(self._validate_output_file)

        if output_format is not None:
            self._selected_output_format = output_format
        else:
            self._selected_output_format = self.valid_output_file_types[0]

        for filetype in self.valid_output_file_types:
            radio = QtWidgets.QRadioButton("." + filetype, typing.cast(QtWidgets.QWidget, self))
            if filetype == self._selected_output_format:
                radio.setChecked(True)
            radio.toggled.connect(self._on_output_format_changed)
            self.output_format_layout.addWidget(radio)

    def _on_output_format_changed(self):
        button = typing.cast(QtWidgets.QWidget, self).sender()
        if button.isChecked():
            self._selected_output_format = button.text()[1:]
            current_filename = Path(self.output_file_edit.text())
            if str(current_filename) != '.':
                self.output_file_edit.setText(str(current_filename.with_suffix('.' + self._selected_output_format)))
                self._validate_output_file()
