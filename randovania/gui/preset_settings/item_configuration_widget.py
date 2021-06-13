from typing import Tuple

from PySide2.QtCore import Signal
from PySide2.QtWidgets import QDialog, QWidget

from randovania.game_description.item.major_item import MajorItem
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.gui.generated.item_configuration_popup_ui import Ui_ItemConfigurationPopup
from randovania.gui.lib.common_qt_lib import set_default_window_icon
from randovania.layout.base.major_item_state import MajorItemState


class ItemConfigurationWidget(QDialog, Ui_ItemConfigurationPopup):
    Changed = Signal()

    def __init__(self, parent: QWidget, item: MajorItem, starting_state: MajorItemState,
                 resources_database: ResourceDatabase):
        super().__init__(parent)
        self.setupUi(self)
        set_default_window_icon(self)
        self._item = item

        self.setWindowTitle(f"Item: {item.name}")
        self.item_name_label.setText(item.name)

        # connect
        self.excluded_radio.toggled.connect(self._on_select_excluded)
        self.vanilla_radio.toggled.connect(self._on_select_vanilla)
        self.starting_radio.toggled.connect(self._on_select_starting)
        self.shuffled_radio.toggled.connect(self._on_select_shuffled)
        self.shuffled_spinbox.valueChanged.connect(self._on_shuffled_value)
        self.provided_ammo_spinbox.valueChanged.connect(self._on_shuffled_value)

        # Update
        self.vanilla_radio.setEnabled(item.original_index is not None)

        if not self.vanilla_radio.isEnabled():
            self.vanilla_radio.setToolTip(
                "This item does not exist in the original game, so there's no vanilla location.")

        # At least one radio should be selected
        for radio in (self.shuffled_radio, self.starting_radio, self.vanilla_radio):
            if radio.isEnabled():
                radio.setChecked(True)
                break

        if item.ammo_index:
            self.provided_ammo_label.setText(
                "<html><head/><body><p>Provided Ammo ({})</p></body></html>".format(
                    " and ".join(
                        resources_database.get_item(ammo_index).long_name
                        for ammo_index in item.ammo_index
                    )
                )
            )
        else:
            self.provided_ammo_label.hide()
            self.provided_ammo_spinbox.hide()

        if self._item.required:
            self.item_name_label.setToolTip(
                "This item is necessary for the game to function properly and can't be removed.")
            self.setEnabled(False)
            self.state = self._create_state(num_included_in_starting_items=1)
        else:
            if self._item.warning is not None:
                self.warning_label.setText(self._item.warning)
            else:
                self.warning_label.setVisible(False)
            self.state = starting_state

    @property
    def item(self):
        return self._item

    @property
    def state(self) -> MajorItemState:
        if not self.excluded_radio.isChecked():
            return MajorItemState(
                include_copy_in_original_location=self.vanilla_radio.isChecked(),
                num_shuffled_pickups=self.shuffled_spinbox.value() if self.shuffled_radio.isChecked() else 0,
                num_included_in_starting_items=1 if self.starting_radio.isChecked() else 0,
                included_ammo=self.included_ammo,
            )
        else:
            return MajorItemState(
                include_copy_in_original_location=False,
                num_shuffled_pickups=0,
                num_included_in_starting_items=0,
                included_ammo=self.included_ammo,
            )

    @state.setter
    def state(self, value: MajorItemState):
        self._update_for_state(value)

    def _update_for_state(self, state):
        self.shuffled_spinbox.setEnabled(False)

        if state.included_ammo:
            self.provided_ammo_spinbox.setValue(state.included_ammo[0])

        if state.include_copy_in_original_location and self.vanilla_radio.isEnabled():
            self.vanilla_radio.setChecked(True)

        elif state.num_shuffled_pickups > 0 and self.shuffled_radio.isEnabled():
            self.shuffled_radio.setChecked(True)
            self.shuffled_spinbox.setEnabled(True)
            self.shuffled_spinbox.setValue(state.num_shuffled_pickups)

        elif state.num_included_in_starting_items > 0:
            self.starting_radio.setChecked(True)

        else:
            self.excluded_radio.setChecked(True)

        self.Changed.emit()

    def button_box_accepted(self):
        self.accept()

    def button_box_rejected(self):
        self.reject()

    def _on_included_box_toggle(self, enabled: bool):
        self._update_for_state(self.state)

    def _on_select_excluded(self, value: bool):
        self._update_for_state(self.state)

    def _on_select_vanilla(self, value: bool):
        self._update_for_state(self.state)

    def _on_select_starting(self, value: bool):
        self._update_for_state(self.state)

    def _on_select_shuffled(self, value: bool):
        self._update_for_state(self.state)

    def _on_shuffled_value(self, value: int):
        self._update_for_state(self.state)

    def _create_state(self,
                      *,
                      include_copy_in_original_location=False,
                      num_shuffled_pickups=0,
                      num_included_in_starting_items=0,
                      ):
        return MajorItemState(
            include_copy_in_original_location=include_copy_in_original_location,
            num_shuffled_pickups=num_shuffled_pickups,
            num_included_in_starting_items=num_included_in_starting_items,
            included_ammo=self.included_ammo,
        )

    @property
    def included_ammo(self) -> Tuple[int, ...]:
        return tuple(
            self.provided_ammo_spinbox.value()
            for _ in self._item.ammo_index
        )
