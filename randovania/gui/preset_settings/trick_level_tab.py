from __future__ import annotations

import functools
from typing import TYPE_CHECKING

from PySide6 import QtCore, QtWidgets

from randovania.game_description.resources.resource_type import ResourceType
from randovania.games.game import RandovaniaGame
from randovania.games.prime1.layout.prime_configuration import PrimeConfiguration
from randovania.gui.dialog.trick_details_popup import BaseResourceDetailsPopup, ResourceDetailsPopup, TrickDetailsPopup
from randovania.gui.generated.preset_trick_level_ui import Ui_PresetTrickLevel
from randovania.gui.lib import signal_handling
from randovania.gui.preset_settings.preset_tab import PresetTab
from randovania.layout.base.trick_level import LayoutTrickLevel
from randovania.layout.lib import trick_lib
from randovania.lib import enum_lib

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.resources.trick_resource_info import TrickResourceInfo
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class TrickSlider(QtWidgets.QSlider):
    """
    A custom implementation of QSlider that filters out mouse wheel events
    """

    def __init__(self, orientation: QtCore.Qt.Orientation, parent: QtWidgets.QWidget | None = None):
        super().__init__(orientation, parent)

    def eventFilter(self, watched: QtCore.QObject, event: QtCore.QEvent) -> bool:
        # filter out "Wheel" type events
        if event.type() == QtCore.QEvent.Type.Wheel:
            event.ignore()
            return True

        return super().eventFilter(watched, event)


class PresetTrickLevel(PresetTab, Ui_PresetTrickLevel):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)

        self.trick_level_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        signal_handling.on_checked(self.underwater_abuse_check, self._on_underwater_abuse_check)
        self.underwater_abuse_label.linkActivated.connect(self._on_click_link_underwater_details)

        self.trick_difficulties_layout = QtWidgets.QGridLayout()
        self._slider_for_trick = {}

        tricks_in_use = trick_lib.used_tricks(self.game_description)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Preferred)

        self.trick_level_line_1.setVisible(self.game_enum != RandovaniaGame.METROID_PRIME_CORRUPTION)
        self.underwater_abuse_label.setText(self.underwater_abuse_label.text().replace("color:#0000ff;", ""))

        if self.game_enum != RandovaniaGame.METROID_PRIME:
            for w in [self.underwater_abuse_check, self.underwater_abuse_label]:
                w.setVisible(False)

        self._create_difficulty_details_row()

        row = 2
        for trick in sorted(self.game_description.resource_database.trick, key=lambda _trick: _trick.long_name):
            if trick not in tricks_in_use or trick.hide_from_ui:
                continue

            if row > 1:
                self.trick_difficulties_layout.addItem(
                    QtWidgets.QSpacerItem(
                        20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding
                    )
                )

            trick_label = QtWidgets.QLabel(self.trick_level_scroll_contents)
            trick_label.setSizePolicy(size_policy)
            trick_label.setWordWrap(True)
            trick_label.setFixedWidth(100)
            trick_label.setText(trick.long_name)
            self.trick_difficulties_layout.addWidget(trick_label, row, 1, 1, 1)

            slider_layout = QtWidgets.QGridLayout()
            slider_layout.setHorizontalSpacing(0)
            for i in range(12):
                slider_layout.setColumnStretch(i, 1)

            horizontal_slider = TrickSlider(self.trick_level_scroll_contents)
            horizontal_slider.installEventFilter(horizontal_slider)  # enables scroll wheel filter
            horizontal_slider.setMaximum(5)
            horizontal_slider.setPageStep(2)
            horizontal_slider.setOrientation(QtCore.Qt.Orientation.Horizontal)
            horizontal_slider.setTickPosition(QtWidgets.QSlider.TickPosition.TicksBelow)
            horizontal_slider.setEnabled(False)
            horizontal_slider.valueChanged.connect(functools.partial(self._on_slide_trick_slider, trick))
            self._slider_for_trick[trick] = horizontal_slider
            slider_layout.addWidget(horizontal_slider, 0, 1, 1, 10)

            used_difficulties = trick_lib.difficulties_for_trick(self.game_description, trick)
            for i, trick_level in enumerate(enum_lib.iterate_enum(LayoutTrickLevel)):
                if trick_level == LayoutTrickLevel.DISABLED or trick_level in used_difficulties:
                    difficulty_label = QtWidgets.QLabel(self.trick_level_scroll_contents)
                    difficulty_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
                    difficulty_label.setText(trick_level.long_name)

                    slider_layout.addWidget(difficulty_label, 1, 2 * i, 1, 2)

            self.trick_difficulties_layout.addLayout(slider_layout, row, 2, 1, 1)

            if self._window_manager is not None:
                tool_button = QtWidgets.QToolButton(self.trick_level_scroll_contents)
                tool_button.setText("?")
                tool_button.clicked.connect(functools.partial(self._open_trick_details_popup, trick))
                self.trick_difficulties_layout.addWidget(tool_button, row, 3, 1, 1)

            row += 1

        self.trick_level_layout.addLayout(self.trick_difficulties_layout)

    @classmethod
    def tab_title(cls) -> str:
        return "Trick Level"

    @classmethod
    def uses_patches_tab(cls) -> bool:
        return False

    @property
    def game_enum(self) -> RandovaniaGame:
        return self.game_description.game

    def on_preset_changed(self, preset: Preset) -> None:
        trick_level_configuration = preset.configuration.trick_level

        for trick, slider in self._slider_for_trick.items():
            assert self._slider_for_trick[trick] is slider
            slider.setValue(trick_level_configuration.level_for_trick(trick).as_number)
            slider.setEnabled(not trick_level_configuration.minimal_logic)

        if self.game_enum == RandovaniaGame.METROID_PRIME:
            assert isinstance(preset.configuration, PrimeConfiguration)
            self.underwater_abuse_check.setChecked(preset.configuration.allow_underwater_movement_without_gravity)

    def _create_difficulty_details_row(self) -> None:
        row = 1

        trick_label = QtWidgets.QLabel(self.trick_level_scroll_contents)
        trick_label.setWordWrap(True)
        trick_label.setText("Difficulty Details")

        self.trick_difficulties_layout.addWidget(trick_label, row, 1, 1, -1)

        slider_layout = QtWidgets.QGridLayout()
        slider_layout.setHorizontalSpacing(0)
        for i in range(12):
            slider_layout.setColumnStretch(i, 1)
        #
        # if self._window_manager is not None:
        #     for i, trick_level in enumerate(LayoutTrickLevel):
        #         if trick_level not in {LayoutTrickLevel.NO_TRICKS, LayoutTrickLevel.MINIMAL_LOGIC}:
        #             tool_button = QtWidgets.QToolButton(self.trick_level_scroll_contents)
        #             tool_button.setText(trick_level.long_name)
        #             tool_button.clicked.connect(functools.partial(self._open_difficulty_details_popup, trick_level))
        #
        #             slider_layout.addWidget(tool_button, 1, 2 * i, 1, 2)

        self.trick_difficulties_layout.addLayout(slider_layout, row, 2, 1, 1)

    def _on_slide_trick_slider(self, trick: TrickResourceInfo, value: int) -> None:
        if self._slider_for_trick[trick].isEnabled():
            with self._editor as options:
                options.set_configuration_field(
                    "trick_level",
                    options.configuration.trick_level.set_level_for_trick(trick, LayoutTrickLevel.from_number(value)),
                )

    def _on_underwater_abuse_check(self, state: bool) -> None:
        with self._editor as options:
            options.set_configuration_field(
                "allow_underwater_movement_without_gravity",
                state,
            )

    def _on_click_link_underwater_details(self, link: str) -> None:
        self._exec_trick_details(
            ResourceDetailsPopup(
                self,
                self._window_manager,
                self.game_description,
                self.game_description.resource_database.get_by_type_and_index(ResourceType.MISC, "NoGravity"),
            )
        )

    def _exec_trick_details(self, popup: BaseResourceDetailsPopup) -> None:
        self._trick_details_popup = popup
        self._trick_details_popup.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
        self._trick_details_popup.open()

    def _open_trick_details_popup(self, trick: TrickResourceInfo) -> None:
        self._exec_trick_details(
            TrickDetailsPopup(
                self,
                self._window_manager,
                self.game_description,
                trick,
                self._editor.configuration.trick_level.level_for_trick(trick),
                self._editor.configuration.trick_level,
            )
        )
