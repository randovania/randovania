import dataclasses

from PySide6 import QtWidgets

from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.preset import Preset


class PresetTab(QtWidgets.QMainWindow):
    def __init__(self, editor: PresetEditor) -> None:
        super().__init__()
        self._editor = editor

    @classmethod
    def tab_title(cls) -> str:
        raise NotImplementedError()

    @classmethod
    def uses_patches_tab(cls) -> bool:
        raise NotImplementedError()

    def on_preset_changed(self, preset: Preset):
        raise NotImplementedError()

    # Persistence helpers
    def _persist_enum(self, combo: QtWidgets.QComboBox, attribute_name: str):
        def persist(index: int):
            with self._editor as options:
                options.set_configuration_field(attribute_name, combo.itemData(index))

        return persist

    def _persist_bool_layout_field(self, field_name: str):
        def bound(value: int):
            with self._editor as editor:
                editor.set_configuration_field(field_name, bool(value))

        return bound

    def _persist_bool_major_configuration_field(self, field_name: str):
        def bound(value: int):
            with self._editor as editor:
                kwargs = {field_name: bool(value)}
                editor.major_items_configuration = dataclasses.replace(editor.major_items_configuration, **kwargs)

        return bound

    def _persist_option_then_notify(self, attribute_name: str):
        def persist(value: int):
            with self._editor as options:
                options.set_configuration_field(attribute_name, bool(value))

        return persist

    def _persist_float(self, attribute_name: str):
        def persist(value: float):
            with self._editor as options:
                options.set_configuration_field(attribute_name, value)

        return persist
