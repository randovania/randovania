import json
import random
from functools import partial

from PySide2.QtCore import Signal
from PySide2.QtWidgets import QDialog, QMessageBox, QWidget

from randovania import get_data_path
from randovania.gui.background_task_mixin import BackgroundTaskMixin
from randovania.gui.main_window_ui import Ui_MainWindow
from randovania.interface_common import simplified_patcher
from randovania.interface_common.options import Options
from randovania.interface_common.status_update_lib import ProgressUpdateCallable
from randovania.layout.layout_configuration import LayoutSkyTempleKeyMode
from randovania.layout.patcher_configuration import PatcherConfiguration
from randovania.resolver.exceptions import GenerationFailure


def show_failed_generation_exception(exception: GenerationFailure):
    QMessageBox.critical(None,
                         "An error occurred while generating a seed",
                         "{}\n\nSome errors are expected to occur, please try again.".format(exception))


class GenerateSeedTab(QWidget):
    _current_lock_state: bool = True
    _logic_settings_window = None

    failed_to_generate_signal = Signal(GenerationFailure)

    def __init__(self, background_processor: BackgroundTaskMixin, window: Ui_MainWindow, options: Options):
        super().__init__()

        self.background_processor = background_processor
        self.window = window
        self._options = options

        self.failed_to_generate_signal.connect(show_failed_generation_exception)

        with get_data_path().joinpath("presets", "presets.json").open() as presets_file:
            self.presets = json.load(presets_file)

    def setup_ui(self):
        window = self.window

        # Progress
        self.background_processor.background_tasks_button_lock_signal.connect(self.enable_buttons_with_background_tasks)

        # Store the original text for the Layout details labels
        for label in [window.create_item_placement_label,
                      window.create_items_label,
                      window.create_difficulty_label,
                      window.create_gameplay_label,
                      window.create_game_changes_label,
                      window.create_sky_temple_keys_label]:
            label.originalText = label.text()

        for preset in self.presets["presets"]:
            with get_data_path().joinpath("presets", preset["path"]).open() as preset_file:
                preset.update(json.load(preset_file))
            window.create_preset_combo.addItem(preset["name"], preset)

        window.create_customize_button.clicked.connect(self._on_customize_button)
        window.create_preset_combo.activated.connect(self._on_select_preset)
        window.create_generate_button.clicked.connect(partial(self._generate_new_seed, True))
        window.create_generate_race_button.clicked.connect(partial(self._generate_new_seed, False))

    def enable_buttons_with_background_tasks(self, value: bool):
        self._current_lock_state = value
        self.window.welcome_tab.setEnabled(value)

    def _create_custom_preset_item(self):
        create_preset_combo = self.window.create_preset_combo

        preset = {
            "name": "Custom",
            "description": "A preset that was customized.",
            "patcher_configuration": self._options.patcher_configuration.as_json,
            "layout_configuration": self._options.layout_configuration.as_json,
        }

        custom_id = create_preset_combo.findText("Custom")
        if custom_id != -1:
            create_preset_combo.removeItem(custom_id)

        create_preset_combo.addItem(preset["name"], preset)
        create_preset_combo.setCurrentIndex(create_preset_combo.count() - 1)
        self.window.create_preset_description.setText(preset["description"])

    def _on_customize_button(self):
        current_preset = self.window.create_preset_combo.currentData()

        from randovania.gui.logic_settings_window import LogicSettingsWindow
        self._logic_settings_window = LogicSettingsWindow(self.window, self._options)
        self._logic_settings_window.on_options_changed(self._options)

        result = self._logic_settings_window.exec_()
        self._logic_settings_window = None

        if result == QDialog.Accepted:
            self._create_custom_preset_item()

        with self._options as options:
            options.set_preset(current_preset)

    def _on_select_preset(self):
        preset_data = self.window.create_preset_combo.currentData()

        self.window.create_preset_description.setText(preset_data["description"])

        with self._options as options:
            options.set_preset(preset_data)

    # Generate seed

    def _generate_new_seed(self, spoiler: bool):
        with self._options as options:
            options.seed_number = random.randint(0, 2 ** 31)
            options.create_spoiler = spoiler

        self._generate_seed()

    def _generate_seed(self):
        def work(progress_update: ProgressUpdateCallable):
            try:
                layout = simplified_patcher.generate_layout(progress_update=progress_update, options=self._options)
                progress_update(f"Success! (Seed hash: {layout.shareable_hash})", 1)
                self.window.show_seed_tab(layout)

            except GenerationFailure as generate_exception:
                self.failed_to_generate_signal.emit(generate_exception)
                progress_update("Generation Failure: {}".format(generate_exception), -1)

        self.background_processor.run_in_background_thread(work, "Creating a seed...")

    def on_options_changed(self, options: Options):
        if self._logic_settings_window is not None:
            self._logic_settings_window.on_options_changed(self._options)
            return

        name = options.selected_preset
        if name is None:
            name = "Custom"

        create_preset_combo = self.window.create_preset_combo
        preset_item = create_preset_combo.findText(name)
        if preset_item == -1:
            self._create_custom_preset_item()
        elif preset_item == create_preset_combo.currentIndex():
            self._on_select_preset()
        else:
            create_preset_combo.setCurrentIndex(preset_item)

        patcher = options.patcher_configuration
        configuration = options.layout_configuration
        major_items = configuration.major_items_configuration

        def _bool_to_str(b: bool) -> str:
            if b:
                return "Yes"
            else:
                return "No"

        # Item Placement

        random_starting_items = "{} to {}".format(
            major_items.minimum_random_starting_items,
            major_items.maximum_random_starting_items,
        )
        if random_starting_items == "0 to 0":
            random_starting_items = "None"

        self.window.create_item_placement_label.setText(
            self.window.create_item_placement_label.originalText.format(
                trick_level=configuration.trick_level_configuration.pretty_description,
                randomization_mode=configuration.randomization_mode.value,
                random_starting_items=random_starting_items,
            )
        )

        # Items
        self.window.create_items_label.setText(
            self.window.create_items_label.originalText.format(
                progressive_suit=_bool_to_str(major_items.progressive_suit),
                progressive_grapple=_bool_to_str(major_items.progressive_grapple),
                split_beam_ammo=_bool_to_str(configuration.split_beam_ammo),
                starting_items="???",
                custom_items="None",
            )
        )

        # Difficulty
        default_patcher = PatcherConfiguration()

        if patcher.varia_suit_damage == default_patcher.varia_suit_damage and (
                patcher.dark_suit_damage == default_patcher.dark_suit_damage):
            dark_aether_suit_damage = "Normal"
        else:
            dark_aether_suit_damage = "Custom"

        self.window.create_difficulty_label.setText(
            self.window.create_difficulty_label.originalText.format(
                dark_aether_suit_damage=dark_aether_suit_damage,
                dark_aether_damage_strictness="Normal",
                pickup_model=patcher.pickup_model_style.value,
            )
        )

        # Gameplay
        translator_gates = "Custom"
        translator_configurations = [
            (configuration.translator_configuration.with_vanilla_actual(), "Vanilla (Actual)"),
            (configuration.translator_configuration.with_vanilla_colors(), "Vanilla (Colors)"),
            (configuration.translator_configuration.with_full_random(), "Random"),
        ]
        for translator_config, name in translator_configurations:
            if translator_config == configuration.translator_configuration:
                translator_gates = name
                break

        self.window.create_gameplay_label.setText(
            self.window.create_gameplay_label.originalText.format(
                starting_location=configuration.starting_location.configuration.value,
                translator_gates=translator_gates,
                elevators=configuration.elevators.value,
                hints="Yes",
            )
        )

        # Game Changes
        missile_launcher_required = True
        main_pb_required = True
        for ammo, state in configuration.ammo_configuration.items_state.items():
            if ammo.name == "Missile Expansion":
                missile_launcher_required = state.requires_major_item
            elif ammo.name == "Power Bomb Expansion":
                main_pb_required = state.requires_major_item

        self.window.create_game_changes_label.setText(
            self.window.create_game_changes_label.originalText.format(
                missile_launcher_required=_bool_to_str(missile_launcher_required),
                main_pb_required=_bool_to_str(main_pb_required),
                warp_to_start=_bool_to_str(patcher.warp_to_start),
                generic_patches="Some",
            )
        )

        # Sky Temple Keys
        if configuration.sky_temple_keys.num_keys == LayoutSkyTempleKeyMode.ALL_BOSSES:
            stk_location = "Bosses"
        elif configuration.sky_temple_keys.num_keys == LayoutSkyTempleKeyMode.ALL_GUARDIANS:
            stk_location = "Guardians"
        else:
            stk_location = "Random"

        self.window.create_sky_temple_keys_label.setText(
            self.window.create_sky_temple_keys_label.originalText.format(
                target="{0} of {0}".format(configuration.sky_temple_keys.num_keys),
                location=stk_location,
            )
        )
