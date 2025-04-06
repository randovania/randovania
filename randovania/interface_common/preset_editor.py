from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING, Any, Self

from randovania.layout.preset import Preset

if TYPE_CHECKING:
    import uuid
    from collections.abc import Callable

    from randovania.game.game_enum import RandovaniaGame
    from randovania.interface_common.options import Options
    from randovania.layout.base.ammo_pickup_configuration import AmmoPickupConfiguration
    from randovania.layout.base.available_locations import AvailableLocationsConfiguration
    from randovania.layout.base.base_configuration import BaseConfiguration
    from randovania.layout.base.damage_strictness import LayoutDamageStrictness
    from randovania.layout.base.dock_rando_configuration import DockRandoConfiguration
    from randovania.layout.base.hint_configuration import HintConfiguration
    from randovania.layout.base.standard_pickup_configuration import StandardPickupConfiguration
    from randovania.layout.lib.teleporters import TeleporterConfiguration


class PresetEditor[Configuration: BaseConfiguration]:
    _on_changed: Callable[[], None] | None = None
    _nested_autosave_level: int = 0
    _is_dirty: bool = False
    _options: Options

    _name: str
    _uuid: uuid.UUID
    _game: RandovaniaGame
    _description: str
    _configuration: Configuration

    def __init__(self, initial_preset: Preset[Configuration], options: Options):
        self._name = initial_preset.name
        self._uuid = initial_preset.uuid
        self._game = initial_preset.game
        self._description = initial_preset.description
        self._configuration = initial_preset.configuration
        self._options = options

    def _set_field(self, field_name: str, value) -> None:
        setattr(self, "_" + field_name, value)

    def __enter__(self) -> Self:
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
    def _set_on_changed(self, value) -> None:
        self._on_changed = value

    on_changed = property(fset=_set_on_changed)

    # Preset

    def create_custom_preset_with(self) -> Preset[Configuration]:
        return Preset(
            name=self.name,
            description=self._description,
            uuid=self._uuid,
            game=self._game,
            configuration=self.configuration,
        )

    # Access to Direct fields
    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._set_field("name", value)

    @property
    def game(self) -> RandovaniaGame:
        return self._game

    @property
    def description(self) -> str:
        return self._description

    @description.setter
    def description(self, value: str) -> None:
        self._set_field("description", value)

    @property
    def configuration(self) -> Configuration:
        return self._configuration

    @property
    def layout_configuration_damage_strictness(self) -> LayoutDamageStrictness:
        return self.configuration.damage_strictness

    @layout_configuration_damage_strictness.setter
    def layout_configuration_damage_strictness(self, value: LayoutDamageStrictness):
        self.set_configuration_field("damage_strictness", value)

    @property
    def layout_configuration_teleporters(self) -> TeleporterConfiguration:
        return self.configuration.teleporters

    @layout_configuration_teleporters.setter
    def layout_configuration_teleporters(self, value: TeleporterConfiguration):
        self.set_configuration_field("teleporters", value)

    @property
    def available_locations(self) -> AvailableLocationsConfiguration:
        return self.configuration.available_locations

    @available_locations.setter
    def available_locations(self, value: AvailableLocationsConfiguration):
        self.set_configuration_field("available_locations", value)

    @property
    def standard_pickup_configuration(self) -> StandardPickupConfiguration:
        return self.configuration.standard_pickup_configuration

    @standard_pickup_configuration.setter
    def standard_pickup_configuration(self, value: StandardPickupConfiguration):
        self.set_configuration_field("standard_pickup_configuration", value)

    @property
    def ammo_pickup_configuration(self) -> AmmoPickupConfiguration:
        return self.configuration.ammo_pickup_configuration

    @ammo_pickup_configuration.setter
    def ammo_pickup_configuration(self, value: AmmoPickupConfiguration):
        self.set_configuration_field("ammo_pickup_configuration", value)

    @property
    def dock_rando_configuration(self) -> DockRandoConfiguration:
        return self.configuration.dock_rando

    @dock_rando_configuration.setter
    def dock_rando_configuration(self, value: DockRandoConfiguration):
        self.set_configuration_field("dock_rando", value)

    @property
    def hint_configuration(self) -> HintConfiguration:
        return self.configuration.hints

    @hint_configuration.setter
    def hint_configuration(self, value: HintConfiguration):
        self.set_configuration_field("hints", value)

    def set_configuration_field(self, field_name: str, value: Any):
        self._edit_field("configuration", dataclasses.replace(self.configuration, **{field_name: value}))

    def set_hint_configuration_field(self, field_name: str, value: Any):
        self.hint_configuration = dataclasses.replace(self.hint_configuration, **{field_name: value})

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
