import datetime
import difflib
import json
from typing import Iterator

from PySide6 import QtWidgets, QtCore
from qasync import asyncSlot

from randovania.gui.generated.preset_history_dialog_ui import Ui_PresetHistoryDialog
from randovania.gui.lib import common_qt_lib, file_prompts
from randovania.interface_common.preset_manager import PresetManager
from randovania.layout import preset_describer
from randovania.layout.preset import Preset
from randovania.layout.versioned_preset import VersionedPreset, InvalidPreset


def _get_old_preset(preset_str: str) -> Preset | str:
    try:
        old_preset = VersionedPreset(json.loads(preset_str))
    except json.JSONDecodeError as e:
        return f"Preset at this version contains json errors: {e}"

    try:
        return old_preset.get_preset()

    except InvalidPreset as e:
        return (
            f"Preset {old_preset.name} at this version can't be used as it contains the following error:"
            f"\n{e.original_exception}"
        )


def _describe_preset(preset: Preset) -> list[str]:
    lines = [
        f"# {preset.name}",
        preset.description,
    ]

    for category, contents in preset_describer.describe(preset):
        lines.append("")
        lines.append(f"## {category}")
        lines.extend(contents)

    return lines


def _calculate_previous_versions(preset_manager: PresetManager, preset: VersionedPreset,
                                 original_lines: tuple[str, ...],
                                 ) -> Iterator[tuple[datetime.datetime, Preset, tuple[str, ...]]]:
    previous_description = None

    for date, commit in preset_manager.get_previous_versions(preset):
        old_preset = _get_old_preset(preset_manager.get_previous_version(preset, commit))
        if not isinstance(old_preset, Preset):
            continue

        old_description = tuple(_describe_preset(old_preset))
        if old_description in (original_lines, previous_description):
            continue

        previous_description = old_description
        yield date, old_preset, old_description


class PresetHistoryDialog(QtWidgets.QDialog, Ui_PresetHistoryDialog):
    def __init__(self, preset_manager: PresetManager, preset: VersionedPreset):
        super().__init__()
        self.setupUi(self)
        common_qt_lib.set_default_window_icon(self)

        self.preset_manager = preset_manager
        self.preset = preset

        try:
            self._original_lines = tuple(_describe_preset(preset.get_preset()))
        except InvalidPreset:
            self._original_lines = None

        item = QtWidgets.QListWidgetItem("Current Version")
        item.setData(QtCore.Qt.UserRole, (None, self._original_lines))
        self.version_widget.addItem(item)

        for date, old_preset, old_description in _calculate_previous_versions(self.preset_manager, self.preset,
                                                                              self._original_lines):
            item = QtWidgets.QListWidgetItem(date.astimezone().strftime("%c"))
            item.setData(QtCore.Qt.UserRole, (old_preset, old_description))
            self.version_widget.addItem(item)

        self.accept_button.clicked.connect(self.accept)
        self.export_button.clicked.connect(self._export_selected_preset)
        self.cancel_button.clicked.connect(self.reject)
        self.version_widget.itemSelectionChanged.connect(self._on_selection_changed)
        self._on_selection_changed()

    def selected_preset(self) -> Preset | None:
        items = self.version_widget.selectedItems()
        if items:
            return items[0].data(QtCore.Qt.UserRole)[0]
        else:
            return None

    @asyncSlot()
    async def _export_selected_preset(self):
        preset = self.selected_preset()
        assert preset is not None

        preset = VersionedPreset.with_preset(preset)
        default_name = f"{preset.slug_name}.rdvpreset"
        path = await file_prompts.prompt_preset(self, new_file=True, name=default_name)
        if path is not None:
            preset.save_to_file(path)

    def _on_selection_changed(self):
        items = self.version_widget.selectedItems()
        self.accept_button.setEnabled(False)
        self.export_button.setEnabled(False)
        if not items:
            self.label.setText("Select a version on the left")
            return

        old_preset, old_description = items[0].data(QtCore.Qt.UserRole)
        self.accept_button.setEnabled(old_preset is not None)
        self.export_button.setEnabled(self.accept_button.isEnabled())

        if old_preset is not None and self._original_lines:
            k = list(difflib.unified_diff(
                self._original_lines,
                old_description,
            ))
            description = "\n\n".join(k[2:])
        else:
            description = "\n\n".join(old_description)

        self.label.setText(description)
