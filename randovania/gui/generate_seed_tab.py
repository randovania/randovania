import random
from functools import partial
from typing import Optional

from PySide2.QtCore import Signal
from PySide2.QtWidgets import QDialog, QMessageBox, QWidget

from randovania.gui.dialog.logic_settings_window import LogicSettingsWindow
from randovania.gui.generated.main_window_ui import Ui_MainWindow
from randovania.gui.lib.background_task_mixin import BackgroundTaskMixin
from randovania.gui.lib.window_manager import WindowManager
from randovania.interface_common import simplified_patcher
from randovania.interface_common.options import Options
from randovania.interface_common.preset_editor import PresetEditor
from randovania.interface_common.preset_manager import PresetManager
from randovania.interface_common.status_update_lib import ProgressUpdateCallable
from randovania.layout.layout_configuration import LayoutSkyTempleKeyMode
from randovania.layout.patcher_configuration import PatcherConfiguration
from randovania.layout.permalink import Permalink
from randovania.layout.preset import Preset
from randovania.resolver.exceptions import GenerationFailure


class GenerateSeedTab(QWidget):
    _current_lock_state: bool = True
    _logic_settings_window = None
    _current_preset: Preset = None

    preset_manager: PresetManager
    failed_to_generate_signal = Signal(GenerationFailure)

    def __init__(self, background_processor: BackgroundTaskMixin, window: Ui_MainWindow,
                 window_manager: WindowManager, options: Options):
        super().__init__()

        self.background_processor = background_processor
        self.window = window
        self._window_manager = window_manager
        self._options = options
        self.preset_manager = PresetManager(options.data_dir)

        self.failed_to_generate_signal.connect(self._show_failed_generation_exception)

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

        for preset in self.preset_manager.all_presets:
            self._create_button_for_preset(preset)

        window.create_customize_button.clicked.connect(self._on_customize_button)
        window.create_delete_button.clicked.connect(self._on_delete_preset_button)
        window.create_preset_combo.activated.connect(self._on_select_preset)
        window.create_generate_button.clicked.connect(partial(self._generate_new_seed, True))
        window.create_generate_race_button.clicked.connect(partial(self._generate_new_seed, False))

    def _show_failed_generation_exception(self, exception: GenerationFailure):
        QMessageBox.critical(self._window_manager,
                             "An error occurred while generating a seed",
                             "{}\n\nSome errors are expected to occur, please try again.".format(exception))

    @property
    def _current_preset_data(self) -> Optional[Preset]:
        return self.preset_manager.preset_for_name(self.window.create_preset_combo.currentData())

    def enable_buttons_with_background_tasks(self, value: bool):
        self._current_lock_state = value
        self.window.welcome_tab.setEnabled(value)

    def _create_button_for_preset(self, preset: Preset):
        create_preset_combo = self.window.create_preset_combo
        create_preset_combo.addItem(preset.name, preset.name)

    def _on_customize_button(self):
        editor = PresetEditor(self._current_preset_data)
        self._logic_settings_window = LogicSettingsWindow(self._window_manager, editor)

        self._logic_settings_window.on_preset_changed(editor.create_custom_preset_with())
        editor.on_changed = lambda: self._logic_settings_window.on_preset_changed(editor.create_custom_preset_with())

        result = self._logic_settings_window.exec_()
        self._logic_settings_window = None

        if result == QDialog.Accepted:
            new_preset = editor.create_custom_preset_with()

            with self._options as options:
                options.selected_preset_name = new_preset.name

            if self.preset_manager.add_new_preset(new_preset):
                self._create_button_for_preset(new_preset)
            self.on_preset_changed(new_preset)

    def _on_delete_preset_button(self):
        self.preset_manager.delete_preset(self._current_preset_data)
        self.window.create_preset_combo.removeItem(self.window.create_preset_combo.currentIndex())
        self._on_select_preset()

    def _on_select_preset(self):
        preset_data = self._current_preset_data
        self.on_preset_changed(preset_data)
        with self._options as options:
            options.selected_preset_name = preset_data.name

    # Generate seed

    def _generate_new_seed(self, spoiler: bool):
        preset = self._current_preset_data
        self.generate_seed_from_permalink(Permalink(
            seed_number=random.randint(0, 2 ** 31),
            spoiler=spoiler,
            patcher_configuration=preset.patcher_configuration,
            layout_configuration=preset.layout_configuration,
        ))

    def generate_seed_from_permalink(self, permalink: Permalink):
        def work(progress_update: ProgressUpdateCallable):
            try:
                layout = simplified_patcher.generate_layout(progress_update=progress_update,
                                                            permalink=permalink,
                                                            options=self._options)
                progress_update(f"Success! (Seed hash: {layout.shareable_hash})", 1)
                self.window.show_seed_tab(layout)

            except GenerationFailure as generate_exception:
                self.failed_to_generate_signal.emit(generate_exception)
                progress_update("Generation Failure: {}".format(generate_exception), -1)

        self.background_processor.run_in_background_thread(work, "Creating a seed...")

    def on_options_changed(self, options: Options):
        if self._current_preset is None:
            preset_name = options.selected_preset_name
            if preset_name is not None:
                index = self.window.create_preset_combo.findText(preset_name)
                if index != -1:
                    self.window.create_preset_combo.setCurrentIndex(index)
                    self.on_preset_changed(self._current_preset_data)
                    return

            self.window.create_preset_combo.setCurrentIndex(0)
            self.on_preset_changed(self.preset_manager.default_preset)

    def on_preset_changed(self, preset: Preset):
        self._current_preset = preset

        self.window.create_preset_description.setText(preset.description)
        self.window.create_delete_button.setEnabled(preset.base_preset_name is not None)

        create_preset_combo = self.window.create_preset_combo
        create_preset_combo.setCurrentIndex(create_preset_combo.findText(preset.name))

        patcher = preset.patcher_configuration
        configuration = preset.layout_configuration
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
                dark_aether_damage_strictness=configuration.damage_strictness.long_name,
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
