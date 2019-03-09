from PySide2.QtWidgets import QDialog, QWidget

from randovania.game_description.item.major_item import MajorItem
from randovania.gui.common_qt_lib import set_default_window_icon
from randovania.gui.item_configuration_popup_ui import Ui_ItemConfigurationPopup
from randovania.interface_common.options import Options
from randovania.layout.major_item_state import MajorItemState


class ItemConfigurationPopup(QDialog, Ui_ItemConfigurationPopup):

    def __init__(self, parent: QWidget, item: MajorItem, options: Options):
        super().__init__(parent)
        self.setupUi(self)
        set_default_window_icon(self)
        self._item = item
        self._options = options

        # setup
        self.item_name_label.setText(f"Item: {item.name}")

        # connect
        self.button_box.accepted.connect(self.button_box_accepted)
        self.button_box.rejected.connect(self.button_box_rejected)
        self.included_box.toggled.connect(self._on_included_box_toggle)
        self.vanilla_radio.toggled.connect(self._on_select_vanilla)
        self.starting_radio.toggled.connect(self._on_select_starting)
        self.shuffled_radio.toggled.connect(self._on_select_shuffled)
        self.shuffled_spinbox.valueChanged.connect(self._on_shuffled_value)

        # Update
        if self._item.required:
            self.included_box.setEnabled(False)
            self.state = self._create_state(num_included_in_starting_items=1)
        else:
            self.state = self._options.layout_configuration.major_items_configuration.items_state[self._item]

    @property
    def state(self) -> MajorItemState:
        return self._state

    @state.setter
    def state(self, value: MajorItemState):
        self._state = value
        self._update_for_state(value)

    def _update_for_state(self, state):
        self.shuffled_spinbox.setEnabled(False)

        if state.include_copy_in_original_location:
            self.vanilla_radio.setChecked(True)

        elif state.num_included_in_starting_items > 0:
            self.starting_radio.setChecked(True)

        elif state.num_shuffled_pickups > 0:
            self.shuffled_radio.setChecked(True)
            self.shuffled_spinbox.setEnabled(True)
            self.shuffled_spinbox.setValue(state.num_shuffled_pickups)

        else:
            self.included_box.setChecked(False)

    def button_box_accepted(self):
        print("button_box_accepted")
        self.accept()

    def button_box_rejected(self):
        self.reject()

    def _on_included_box_toggle(self, enabled: bool):
        if enabled:
            self.state = self._last_enabled_state
        else:
            self._last_enabled_state = self.state
            self.state = self._create_state()

    def _on_select_vanilla(self, value: bool):
        if value:
            self.state = self._create_state(include_copy_in_original_location=True)

    def _on_select_starting(self, value: bool):
        if value:
            self.state = self._create_state(num_included_in_starting_items=1)

    def _on_select_shuffled(self, value: bool):
        if value:
            self.state = self._create_state(num_shuffled_pickups=self.shuffled_spinbox.value())

    def _on_shuffled_value(self, value: int):
        self.state = self._create_state(num_shuffled_pickups=value)

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
    def included_ammo(self):
        return ()
