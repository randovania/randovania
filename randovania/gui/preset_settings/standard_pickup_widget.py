from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6 import QtWidgets
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QGraphicsOpacityEffect, QWidget

from randovania.gui.generated.standard_pickup_widget_ui import Ui_StandardPickupWidget
from randovania.gui.lib.signal_handling import set_combo_with_value
from randovania.layout.base import standard_pickup_state
from randovania.layout.base.standard_pickup_state import StandardPickupState, StandardPickupStateCase
from randovania.lib import enum_lib

if TYPE_CHECKING:
    from randovania.game_description.pickup.standard_pickup import StandardPickupDefinition
    from randovania.game_description.resources.resource_database import ResourceDatabase


class StandardPickupWidget(QWidget, Ui_StandardPickupWidget):
    Changed = Signal()

    def __init__(
        self,
        parent: QWidget,
        pickup: StandardPickupDefinition,
        starting_state: StandardPickupState,
        resources_database: ResourceDatabase,
    ):
        super().__init__(parent)
        self.setupUi(self)
        self._pickup = pickup

        self.pickup_name_label.setText(pickup.name)

        # Apply transparency on the separator line
        transparent = QGraphicsOpacityEffect(self.separator_line)
        transparent.setOpacity(0.33)
        self.separator_line.setGraphicsEffect(transparent)
        self.separator_line.hide()

        for case in enum_lib.iterate_enum(StandardPickupStateCase):
            if case == StandardPickupStateCase.VANILLA and pickup.original_location is None:
                continue
            if case == StandardPickupStateCase.STARTING_ITEM and len(pickup.progression) > 1:
                continue

            if case == StandardPickupStateCase.SHUFFLED and pickup.default_shuffled_count > 1:
                text = f"{pickup.default_shuffled_count} shuffled copies"
            elif case == StandardPickupStateCase.STARTING_ITEM and pickup.default_starting_count > 1:
                text = f"{pickup.default_starting_count} starting copies"
            else:
                text = case.pretty_text
            self.state_case_combo.addItem(text, case)

        self.priority_combo.addItem("Very Low", 0.25)
        self.priority_combo.addItem("Low", 0.50)
        self.priority_combo.addItem("Normal", 1.0)
        self.priority_combo.addItem("High", 1.5)
        self.priority_combo.addItem("Very High", 2.0)
        set_combo_with_value(self.priority_combo, 1.0)

        # connect
        self.state_case_combo.currentIndexChanged.connect(self._on_select_case)
        self.vanilla_check.toggled.connect(self._on_select)
        self.starting_check.toggled.connect(self._on_select)
        self.shuffled_spinbox.valueChanged.connect(self._on_select)
        self.shuffled_spinbox.setMaximum(standard_pickup_state.DEFAULT_MAXIMUM_SHUFFLED[-1])
        self.provided_ammo_spinbox.valueChanged.connect(self._on_select)
        self.priority_combo.currentIndexChanged.connect(self._on_select)

        # Update
        self.vanilla_check.setEnabled(pickup.original_location is not None)
        if not self.vanilla_check.isEnabled():
            self.vanilla_check.setToolTip(
                "This item does not exist in the original game, so there's no vanilla location."
            )

        self.starting_check.setEnabled(len(pickup.progression) <= 1)
        if not self.starting_check.isEnabled():
            self.starting_check.setToolTip("Progressive items are not allowed to be marked as starting.")

        if pickup.ammo:
            ammo_names = " and ".join(resources_database.get_item(ammo_index).long_name for ammo_index in pickup.ammo)
            self.provided_ammo_label.setText(
                f"<html><head/><body><p>{ammo_names} provided by {pickup.name}</p></body></html>"
            )
            self.provided_ammo_spinbox.setMaximum(
                min(resources_database.get_item(ammo_index).max_capacity for ammo_index in pickup.ammo)
            )
        else:
            self.provided_ammo_label.hide()
            self.provided_ammo_spinbox.hide()

        if self._pickup.description is not None:
            self.description_label = QtWidgets.QLabel(self._pickup.description, self)
            self.description_label.setWordWrap(True)
            self.root_layout.addWidget(self.description_label, self.root_layout.rowCount(), 0, 1, -1)

        self.set_custom_fields_visible(False)
        if self._pickup.must_be_starting:
            self.pickup_name_label.setToolTip(
                "This item is necessary for the game to function properly and can't be removed."
            )
            self.case = StandardPickupStateCase.STARTING_ITEM
            self.state_case_combo.setEnabled(False)
        else:
            self.set_new_state(starting_state)

    def set_custom_fields_visible(self, visible: bool):
        for item in [
            self.vanilla_check,
            self.starting_check,
            self.priority_label,
            self.priority_combo,
            self.shuffled_spinbox,
        ]:
            item.setVisible(visible)

    @property
    def pickup(self):
        return self._pickup

    @property
    def case(self) -> StandardPickupStateCase:
        return self.state_case_combo.currentData()

    @case.setter
    def case(self, value: StandardPickupStateCase):
        new_index = self.state_case_combo.findData(value)
        if new_index != self.state_case_combo.currentIndex():
            assert self.state_case_combo.isEnabled() or not self.isEnabled(), "Can't set case when locked"
            self.state_case_combo.setCurrentIndex(new_index)
        else:
            self._on_select_case(new_index)

    def _state_from_case(self, case: StandardPickupStateCase, included_ammo) -> StandardPickupState | None:
        if case == StandardPickupStateCase.MISSING:
            return StandardPickupState(included_ammo=included_ammo)

        elif case == StandardPickupStateCase.VANILLA:
            return StandardPickupState(include_copy_in_original_location=True, included_ammo=included_ammo)

        elif case == StandardPickupStateCase.STARTING_ITEM:
            return StandardPickupState(
                num_included_in_starting_pickups=self._pickup.default_starting_count, included_ammo=included_ammo
            )

        elif case == StandardPickupStateCase.SHUFFLED:
            return StandardPickupState(
                num_shuffled_pickups=self._pickup.default_shuffled_count, included_ammo=included_ammo
            )

        else:
            return None

    def _case_from_state(self, state: StandardPickupState) -> StandardPickupStateCase:
        for case in enum_lib.iterate_enum(StandardPickupStateCase):
            if state == self._state_from_case(case, state.included_ammo):
                return case

        return StandardPickupStateCase.CUSTOM

    @property
    def state(self) -> StandardPickupState:
        if self.case == StandardPickupStateCase.CUSTOM:
            return StandardPickupState(
                include_copy_in_original_location=self.vanilla_check.isChecked(),
                num_shuffled_pickups=self.shuffled_spinbox.value(),
                num_included_in_starting_pickups=1 if self.starting_check.isChecked() else 0,
                priority=self.priority_combo.currentData(),
                included_ammo=self.included_ammo,
            )
        else:
            return self._state_from_case(self.case, self.included_ammo)

    def set_new_state(self, value: StandardPickupState):
        if self.state != value:
            self.case = self._case_from_state(value)
            self._update_for_state(value)

    def _update_for_state(self, state):
        if state.included_ammo:
            self.provided_ammo_spinbox.setValue(state.included_ammo[0])

        self.vanilla_check.setChecked(state.include_copy_in_original_location)
        self.shuffled_spinbox.setValue(state.num_shuffled_pickups)
        self.starting_check.setChecked(state.num_included_in_starting_pickups > 0)

        priority_index = self.priority_combo.findData(state.priority)
        if priority_index >= 0:
            self.priority_combo.setCurrentIndex(priority_index)

        self.Changed.emit()

    def _on_select_case(self, _):
        self.set_custom_fields_visible(self.case == StandardPickupStateCase.CUSTOM)
        self.Changed.emit()

    def _on_select(self, value):
        self._update_for_state(self.state)

    @property
    def included_ammo(self) -> tuple[int, ...]:
        return tuple(self.provided_ammo_spinbox.value() for _ in self._pickup.ammo)
