from typing import Tuple

from PySide2.QtWidgets import QDialog, QWidget

from randovania.game_description import default_database
from randovania.game_description.item.major_item import MajorItem
from randovania.game_description.resource_type import ResourceType
from randovania.gui.common_qt_lib import set_default_window_icon
from randovania.gui.item_configuration_popup_ui import Ui_ItemConfigurationPopup
from randovania.layout.major_item_state import MajorItemState

_INVALID_MODELS = {
    0, 1, 9, 10, 16,
}


class ItemConfigurationPopup(QDialog, Ui_ItemConfigurationPopup):

    def __init__(self, parent: QWidget, item: MajorItem, starting_state: MajorItemState):
        super().__init__(parent)
        self.setupUi(self)
        set_default_window_icon(self)
        self._item = item

        # setup
        self.setWindowTitle(f"Item: {item.name}")
        self.warning_label.hide()

        # connect
        self.button_box.accepted.connect(self.button_box_accepted)
        self.button_box.rejected.connect(self.button_box_rejected)
        self.included_box.toggled.connect(self._on_included_box_toggle)
        self.vanilla_radio.toggled.connect(self._on_select_vanilla)
        self.starting_radio.toggled.connect(self._on_select_starting)
        self.shuffled_radio.toggled.connect(self._on_select_shuffled)
        self.shuffled_spinbox.valueChanged.connect(self._on_shuffled_value)

        # Update
        self.vanilla_radio.setEnabled(item.original_index is not None)
        self.shuffled_radio.setEnabled(item.model_index not in _INVALID_MODELS)

        if not self.vanilla_radio.isEnabled():
            self.vanilla_radio.setToolTip(
                "This item does not exist in the original game, so there's no vanilla location.")

        if not self.shuffled_radio.isEnabled():
            self.shuffled_radio.setToolTip(
                "There's currently no available model and/or logic for this item to be shuffled.")

        # At least one radio should be selected
        for radio in (self.shuffled_radio, self.starting_radio, self.vanilla_radio):
            if radio.isEnabled():
                radio.setChecked(True)
                break

        if item.ammo_index:
            resources_database = default_database.default_prime2_resource_database()
            self.provided_ammo_label.setText(
                "<html><head/><body><p>Provided Ammo</p><p>({})</p></body></html>".format(
                    " and ".join(
                        resources_database.get_by_type_and_index(ResourceType.ITEM, ammo_index).long_name
                        for ammo_index in item.ammo_index
                    )
                )
            )
        else:
            self.provided_ammo_label.hide()
            self.provided_ammo_spinbox.hide()

        if self._item.required:
            self.warning_label.setText("This item is necessary for the game to function properly and can't be removed.")
            self.warning_label.show()
            self.included_box.setEnabled(False)
            self.state = self._create_state(num_included_in_starting_items=1)
        else:
            self.state = starting_state

    @property
    def state(self) -> MajorItemState:
        if self.included_box.isChecked():
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
            self.included_box.setChecked(False)

    def button_box_accepted(self):
        self.accept()

    def button_box_rejected(self):
        self.reject()

    def _on_included_box_toggle(self, enabled: bool):
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
