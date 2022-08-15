from PySide6 import QtWidgets
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QGraphicsOpacityEffect, QWidget

from randovania.game_description.item.major_item import MajorItem
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.gui.generated.item_configuration_popup_ui import Ui_ItemConfigurationPopup
from randovania.layout.base.major_item_state import MajorItemState, MajorItemStateCase, DEFAULT_MAXIMUM_SHUFFLED
from randovania.lib import enum_lib


class ItemConfigurationWidget(QWidget, Ui_ItemConfigurationPopup):
    Changed = Signal()

    def __init__(self, parent: QWidget, item: MajorItem, starting_state: MajorItemState,
                 resources_database: ResourceDatabase):
        super().__init__(parent)
        self.setupUi(self)
        self._item = item

        self.item_name_label.setText(item.name)

        # Apply transparency on the separator line
        transparent = QGraphicsOpacityEffect(self.separator_line)
        transparent.setOpacity(0.33)
        self.separator_line.setGraphicsEffect(transparent)
        self.separator_line.hide()

        for case in enum_lib.iterate_enum(MajorItemStateCase):
            if case == MajorItemStateCase.VANILLA and item.original_index is None:
                continue
            if case == MajorItemStateCase.STARTING_ITEM and len(item.progression) > 1:
                continue

            if case == MajorItemStateCase.SHUFFLED and item.default_shuffled_count > 1:
                text = f"{item.default_shuffled_count} shuffled copies"
            elif case == MajorItemStateCase.STARTING_ITEM and item.default_starting_count > 1:
                text = f"{item.default_starting_count} starting copies"
            else:
                text = case.pretty_text
            self.state_case_combo.addItem(text, case)

        self.priority_combo.addItem("Very Low", 0.25)
        self.priority_combo.addItem("Low", 0.50)
        self.priority_combo.addItem("Normal", 1.0)
        self.priority_combo.addItem("High", 1.5)
        self.priority_combo.addItem("Very High", 2.0)
        self.priority_combo.setCurrentIndex(self.priority_combo.findData(1.0))

        # connect
        self.state_case_combo.currentIndexChanged.connect(self._on_select_case)
        self.vanilla_check.toggled.connect(self._on_select)
        self.starting_check.toggled.connect(self._on_select)
        self.shuffled_spinbox.valueChanged.connect(self._on_select)
        self.shuffled_spinbox.setMaximum(DEFAULT_MAXIMUM_SHUFFLED[-1])
        self.provided_ammo_spinbox.valueChanged.connect(self._on_select)
        self.priority_combo.currentIndexChanged.connect(self._on_select)

        # Update
        self.vanilla_check.setEnabled(item.original_index is not None)
        if not self.vanilla_check.isEnabled():
            self.vanilla_check.setToolTip(
                "This item does not exist in the original game, so there's no vanilla location."
            )

        self.starting_check.setEnabled(len(item.progression) <= 1)
        if not self.starting_check.isEnabled():
            self.starting_check.setToolTip("Progressive items are not allowed to be marked as starting.")

        if item.ammo_index:
            ammo_names = " and ".join(
                resources_database.get_item(ammo_index).long_name for ammo_index in item.ammo_index)
            self.provided_ammo_label.setText(
                f"<html><head/><body><p>{ammo_names} provided by {item.name}</p></body></html>"
            )
            self.provided_ammo_spinbox.setMaximum(min(
                resources_database.get_item(ammo_index).max_capacity
                for ammo_index in item.ammo_index
            ))
        else:
            self.provided_ammo_label.hide()
            self.provided_ammo_spinbox.hide()

        if self._item.warning is not None:
            self.warning_label = QtWidgets.QLabel(self._item.warning, self)
            self.warning_label.setWordWrap(True)
            self.root_layout.addWidget(self.warning_label, self.root_layout.rowCount(), 0, 1, -1)

        self.set_custom_fields_visible(False)
        if self._item.must_be_starting:
            self.item_name_label.setToolTip(
                "This item is necessary for the game to function properly and can't be removed.")
            self.case = MajorItemStateCase.STARTING_ITEM
            self.state_case_combo.setEnabled(False)
        else:
            self.set_new_state(starting_state)

    def set_custom_fields_visible(self, visible: bool):
        for item in [self.vanilla_check, self.starting_check, self.priority_label,
                     self.priority_combo, self.shuffled_spinbox]:
            item.setVisible(visible)

    @property
    def item(self):
        return self._item

    @property
    def case(self) -> MajorItemStateCase:
        return self.state_case_combo.currentData()

    @case.setter
    def case(self, value: MajorItemStateCase):
        new_index = self.state_case_combo.findData(value)
        if new_index != self.state_case_combo.currentIndex():
            assert self.state_case_combo.isEnabled() or not self.isEnabled(), "Can't set case when locked"
            self.state_case_combo.setCurrentIndex(new_index)
        else:
            self._on_select_case(new_index)

    def _state_from_case(self, case: MajorItemStateCase, included_ammo) -> MajorItemState | None:
        if case == MajorItemStateCase.MISSING:
            return MajorItemState(included_ammo=included_ammo)

        elif case == MajorItemStateCase.VANILLA:
            return MajorItemState(include_copy_in_original_location=True, included_ammo=included_ammo)

        elif case == MajorItemStateCase.STARTING_ITEM:
            return MajorItemState(num_included_in_starting_items=1, included_ammo=included_ammo)

        elif case == MajorItemStateCase.SHUFFLED:
            return MajorItemState(num_shuffled_pickups=len(self._item.progression),
                                  included_ammo=included_ammo)

        else:
            return None

    def _case_from_state(self, state: MajorItemState) -> MajorItemStateCase:
        for case in enum_lib.iterate_enum(MajorItemStateCase):
            if state == self._state_from_case(case, state.included_ammo):
                return case

        return MajorItemStateCase.CUSTOM

    @property
    def state(self) -> MajorItemState:
        if self.case == MajorItemStateCase.CUSTOM:
            return MajorItemState(
                include_copy_in_original_location=self.vanilla_check.isChecked(),
                num_shuffled_pickups=self.shuffled_spinbox.value(),
                num_included_in_starting_items=1 if self.starting_check.isChecked() else 0,
                priority=self.priority_combo.currentData(),
                included_ammo=self.included_ammo,
            )
        else:
            return self._state_from_case(self.case, self.included_ammo)

    def set_new_state(self, value: MajorItemState):
        if self.state != value:
            self.case = self._case_from_state(value)
            self._update_for_state(value)

    def _update_for_state(self, state):
        if state.included_ammo:
            self.provided_ammo_spinbox.setValue(state.included_ammo[0])

        self.vanilla_check.setChecked(state.include_copy_in_original_location)
        self.shuffled_spinbox.setValue(state.num_shuffled_pickups)
        self.starting_check.setChecked(state.num_included_in_starting_items > 0)

        priority_index = self.priority_combo.findData(state.priority)
        if priority_index >= 0:
            self.priority_combo.setCurrentIndex(priority_index)

        self.Changed.emit()

    def button_box_accepted(self):
        self.accept()

    def button_box_rejected(self):
        self.reject()

    def _on_select_case(self, _):
        self.set_custom_fields_visible(self.case == MajorItemStateCase.CUSTOM)
        self.Changed.emit()

    def _on_select(self, value):
        self._update_for_state(self.state)

    @property
    def included_ammo(self) -> tuple[int, ...]:
        return tuple(
            self.provided_ammo_spinbox.value()
            for _ in self._item.ammo_index
        )
