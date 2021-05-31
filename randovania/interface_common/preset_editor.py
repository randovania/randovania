import dataclasses
import uuid
from typing import Optional, Callable, Union

from randovania.games.game import RandovaniaGame
from randovania.layout.base.ammo_configuration import AmmoConfiguration
from randovania.layout.base.available_locations import AvailableLocationsConfiguration
from randovania.layout.game_to_class import AnyGameConfiguration
from randovania.layout.prime3.corruption_configuration import CorruptionConfiguration
from randovania.layout.base.damage_strictness import LayoutDamageStrictness
from randovania.layout.prime2.echoes_configuration import EchoesConfiguration, LayoutSkyTempleKeyMode
from randovania.layout.base.major_items_configuration import MajorItemsConfiguration
from randovania.layout.preset import Preset
from randovania.layout.lib.teleporters import TeleporterConfiguration


class PresetEditor:
    _on_changed: Optional[Callable[[], None]] = None
    _nested_autosave_level: int = 0
    _is_dirty: bool = False

    _name: str
    _uuid: uuid.UUID
    _base_preset_uuid: uuid.UUID
    _game: RandovaniaGame
    _configuration: AnyGameConfiguration

    def __init__(self, initial_preset: Preset):
        if initial_preset.base_preset_uuid is None:
            raise ValueError("Unable to edit an included preset!")

        self._name = initial_preset.name
        self._uuid = initial_preset.uuid
        self._base_preset_uuid = initial_preset.base_preset_uuid
        self._game = initial_preset.game
        self._configuration = initial_preset.configuration

    def _set_field(self, field_name: str, value):
        setattr(self, "_" + field_name, value)

    def __enter__(self):
        self._nested_autosave_level += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._nested_autosave_level == 1:
            if self._is_dirty:
                # TODO: maybe it should be an error to change options to different values in on_options_changed?
                if self._on_changed is not None:
                    self._on_changed()
        self._nested_autosave_level -= 1

    # Events
    def _set_on_changed(self, value):
        self._on_changed = value

    on_changed = property(fset=_set_on_changed)

    # Preset

    def create_custom_preset_with(self) -> Preset:
        return Preset(
            name=self.name,
            description="A preset that was customized.",
            uuid=self._uuid,
            base_preset_uuid=self._base_preset_uuid,
            game=self._game,
            configuration=self.configuration,
        )

    # Access to Direct fields
    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value):
        self._set_field("name", value)

    @property
    def game(self):
        return self._game

    @property
    def configuration(self) -> AnyGameConfiguration:
        return self._configuration

    # Access to fields inside PatcherConfiguration
    @property
    def include_menu_mod(self) -> bool:
        return self.configuration.menu_mod

    @include_menu_mod.setter
    def include_menu_mod(self, value: bool):
        self.set_configuration_field("menu_mod", value)

    @property
    def warp_to_start(self) -> bool:
        return self.configuration.warp_to_start

    @warp_to_start.setter
    def warp_to_start(self, value: bool):
        self.set_configuration_field("warp_to_start", value)

    @property
    def pickup_model_style(self):
        return self.configuration.pickup_model_style

    @pickup_model_style.setter
    def pickup_model_style(self, value):
        self.set_configuration_field("pickup_model_style", value)

    @property
    def pickup_model_data_source(self):
        return self.configuration.pickup_model_data_source

    @pickup_model_data_source.setter
    def pickup_model_data_source(self, value):
        self.set_configuration_field("pickup_model_data_source", value)

    @property
    def layout_configuration_sky_temple_keys(self) -> LayoutSkyTempleKeyMode:
        return self.configuration.sky_temple_keys

    @layout_configuration_sky_temple_keys.setter
    def layout_configuration_sky_temple_keys(self, value: LayoutSkyTempleKeyMode):
        self.set_configuration_field("sky_temple_keys", value)

    @property
    def layout_configuration_damage_strictness(self) -> LayoutDamageStrictness:
        return self.configuration.damage_strictness

    @layout_configuration_damage_strictness.setter
    def layout_configuration_damage_strictness(self, value: LayoutDamageStrictness):
        self.set_configuration_field("damage_strictness", value)

    @property
    def layout_configuration_elevators(self) -> TeleporterConfiguration:
        return self.configuration.elevators

    @layout_configuration_elevators.setter
    def layout_configuration_elevators(self, value: TeleporterConfiguration):
        self.set_configuration_field("elevators", value)

    @property
    def available_locations(self) -> AvailableLocationsConfiguration:
        return self.configuration.available_locations

    @available_locations.setter
    def available_locations(self, value: AvailableLocationsConfiguration):
        self.set_configuration_field("available_locations", value)

    @property
    def major_items_configuration(self) -> MajorItemsConfiguration:
        return self.configuration.major_items_configuration

    @major_items_configuration.setter
    def major_items_configuration(self, value: MajorItemsConfiguration):
        self.set_configuration_field("major_items_configuration", value)

    @property
    def ammo_configuration(self) -> AmmoConfiguration:
        return self.configuration.ammo_configuration

    @ammo_configuration.setter
    def ammo_configuration(self, value: AmmoConfiguration):
        self.set_configuration_field("ammo_configuration", value)

    def set_configuration_field(self, field_name: str, value):
        self._edit_field(
            "configuration",
            dataclasses.replace(self.configuration, **{field_name: value})
        )

    ######

    def _check_editable_and_mark_dirty(self):
        """Checks if _nested_autosave_level is not 0 and marks at least one value was changed."""
        assert self._nested_autosave_level != 0, "Attempting to edit an PresetEditor, but it wasn't made editable"
        self._is_dirty = True

    def _edit_field(self, field_name: str, new_value):
        current_value = getattr(self, field_name)
        if current_value != new_value:
            self._check_editable_and_mark_dirty()
            self._set_field(field_name, new_value)
