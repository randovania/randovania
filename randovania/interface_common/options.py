import dataclasses
import json
from pathlib import Path
from typing import Optional, TypeVar, Callable, Any, Dict

from randovania.game_description.resources import PickupEntry
from randovania.interface_common import persistence
from randovania.interface_common.persisted_options import get_persisted_options_from_data, serialized_data_for_options
from randovania.resolver.layout_configuration import LayoutConfiguration, LayoutRandomizedFlag, LayoutEnabledFlag, \
    LayoutTrickLevel, LayoutSkyTempleKeyMode
from randovania.resolver.patcher_configuration import PatcherConfiguration
from randovania.resolver.permalink import Permalink

T = TypeVar("T")


def identity(v: T) -> T:
    return v


@dataclasses.dataclass(frozen=True)
class Serializer:
    encode: Callable[[Any], Any]
    decode: Callable[[Any], Any]


_SERIALIZER_FOR_FIELD = {
    "show_advanced_options": Serializer(identity, bool),
    "create_spoiler": Serializer(identity, bool),
    "output_directory": Serializer(str, Path),
    "patcher_configuration": Serializer(lambda p: p.as_json, PatcherConfiguration.from_json_dict),
    "layout_configuration": Serializer(lambda p: p.as_json, LayoutConfiguration.from_json_dict),
}


def _return_with_default(value: Optional[T], default_factory: Callable[[], T]) -> T:
    """
    Returns the given value is if it's not None, otherwise call default_factory
    :param value:
    :param default_factory:
    :return:
    """
    if value is None:
        return default_factory()
    else:
        return value


class Options:
    _data_dir: Path
    _on_options_changed: Optional[Callable[[], None]] = None
    _nested_autosave_level: int = 0
    _is_dirty: bool = False

    _show_advanced_options: Optional[bool] = None
    _seed_number: Optional[int] = None
    _create_spoiler: Optional[bool] = None
    _output_directory: Optional[Path] = None
    _patcher_configuration: Optional[PatcherConfiguration] = None
    _layout_configuration: Optional[LayoutConfiguration] = None

    def __init__(self, data_dir: Path):
        self._data_dir = data_dir

    @classmethod
    def with_default_data_dir(cls) -> "Options":
        return cls(persistence.user_data_dir())

    def _read_persisted_options(self) -> Optional[dict]:
        try:
            with self._data_dir.joinpath("config.json").open() as options_file:
                return json.load(options_file)
        except FileNotFoundError:
            return None

    def _set_field(self, field_name: str, value):
        setattr(self, "_" + field_name, value)

    def load_from_disk(self):
        persisted_data = self._read_persisted_options()
        if persisted_data is None:
            return

        persisted_options = get_persisted_options_from_data(persisted_data)
        for field_name, serializer in _SERIALIZER_FOR_FIELD.items():
            value = persisted_options.get(field_name, None)
            if value is not None:
                self._set_field(field_name, serializer.decode(value))

    def _serialize_fields(self) -> dict:
        data_to_persist = {}
        for field_name, serializer in _SERIALIZER_FOR_FIELD.items():
            value = getattr(self, "_" + field_name, None)
            if value is not None:
                data_to_persist[field_name] = serializer.encode(value)

        return serialized_data_for_options(data_to_persist)

    def _save_to_disk(self):
        """Serializes the fields of this Option and writes then to a file."""
        self._is_dirty = False
        data_to_persist = self._serialize_fields()

        self._data_dir.mkdir(parents=True, exist_ok=True)
        with self._data_dir.joinpath("config.json").open("w") as options_file:
            json.dump(data_to_persist, options_file,
                      indent=4, separators=(',', ': '))

    def __enter__(self):
        self._nested_autosave_level += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._nested_autosave_level == 1:
            if self._is_dirty:
                # TODO: maybe it should be an error to change options to different values in on_options_changed?
                # previous = self._serialize_fields()
                if self._on_options_changed is not None:
                    self._on_options_changed()
                # assert previous == self._serialize_fields()
                self._save_to_disk()
        self._nested_autosave_level -= 1

    # Events
    def _set_on_options_changed(self, value):
        self._on_options_changed = value

    on_options_changed = property(fset=_set_on_options_changed)

    # Reset

    def reset_to_defaults(self):
        self._check_editable_and_mark_dirty()
        self._show_advanced_options = None
        self._create_spoiler = None
        self._patcher_configuration = None
        self._layout_configuration = None

    # Files paths

    @property
    def backup_files_path(self) -> Path:
        return self._data_dir.joinpath("backup")

    @property
    def game_files_path(self) -> Path:
        return self._data_dir.joinpath("extracted_game")

    # Access to Direct fields
    @property
    def seed_number(self) -> Optional[int]:
        return self._seed_number

    @seed_number.setter
    def seed_number(self, value: Optional[int]):
        self._check_editable_and_mark_dirty()
        self._seed_number = value

    @property
    def create_spoiler(self) -> bool:
        return _return_with_default(self._create_spoiler, lambda: True)

    @create_spoiler.setter
    def create_spoiler(self, value: bool):
        self._check_editable_and_mark_dirty()
        self._create_spoiler = value

    @property
    def output_directory(self) -> Optional[Path]:
        return self._output_directory

    @output_directory.setter
    def output_directory(self, value: Optional[Path]):
        self._check_editable_and_mark_dirty()
        self._output_directory = value

    @property
    def patcher_configuration(self) -> PatcherConfiguration:
        return _return_with_default(self._patcher_configuration, PatcherConfiguration.default)

    @property
    def layout_configuration(self) -> LayoutConfiguration:
        return _return_with_default(self._layout_configuration, LayoutConfiguration.default)

    # Permalink
    @property
    def permalink(self) -> Optional[Permalink]:
        if self.seed_number is None:
            return None

        return Permalink(
            seed_number=self.seed_number,
            spoiler=self.create_spoiler,
            patcher_configuration=self.patcher_configuration,
            layout_configuration=self.layout_configuration,
        )

    @permalink.setter
    def permalink(self, value: Permalink):
        self._check_editable_and_mark_dirty()
        self._seed_number = value.seed_number
        self._create_spoiler = value.spoiler
        self._patcher_configuration = value.patcher_configuration
        self._layout_configuration = value.layout_configuration

    # Access to fields inside PatcherConfiguration

    @property
    def hud_memo_popup_removal(self) -> bool:
        return self.patcher_configuration.disable_hud_popup

    @hud_memo_popup_removal.setter
    def hud_memo_popup_removal(self, value: bool):
        self._check_editable_and_mark_dirty()
        self._patcher_configuration = dataclasses.replace(self.patcher_configuration, disable_hud_popup=value)

    @property
    def include_menu_mod(self) -> bool:
        return self.patcher_configuration.menu_mod

    @include_menu_mod.setter
    def include_menu_mod(self, value: bool):
        self._check_editable_and_mark_dirty()
        self._patcher_configuration = dataclasses.replace(self.patcher_configuration, menu_mod=value)

    # Access to fields inside LayoutConfiguration

    @property
    def layout_configuration_trick_level(self) -> LayoutTrickLevel:
        return self.layout_configuration.trick_level

    @layout_configuration_trick_level.setter
    def layout_configuration_trick_level(self, value: LayoutTrickLevel):
        self._check_editable_and_mark_dirty()
        self._layout_configuration = dataclasses.replace(self.layout_configuration, trick_level=value)

    @property
    def layout_configuration_sky_temple_keys(self) -> LayoutSkyTempleKeyMode:
        return self.layout_configuration.sky_temple_keys

    @layout_configuration_sky_temple_keys.setter
    def layout_configuration_sky_temple_keys(self, value: LayoutSkyTempleKeyMode):
        self._check_editable_and_mark_dirty()
        self._layout_configuration = dataclasses.replace(self.layout_configuration, sky_temple_keys=value)

    @property
    def layout_configuration_elevators(self) -> LayoutRandomizedFlag:
        return self.layout_configuration.elevators

    @layout_configuration_elevators.setter
    def layout_configuration_elevators(self, value: LayoutRandomizedFlag):
        self._check_editable_and_mark_dirty()
        self._layout_configuration = dataclasses.replace(self.layout_configuration, elevators=value)

    @property
    def layout_configuration_item_loss(self) -> LayoutEnabledFlag:
        return self.layout_configuration.item_loss

    @layout_configuration_item_loss.setter
    def layout_configuration_item_loss(self, value: LayoutEnabledFlag):
        self._check_editable_and_mark_dirty()
        self._layout_configuration = dataclasses.replace(self.layout_configuration, item_loss=value)

    def quantity_for_pickup(self, pickup: PickupEntry) -> int:
        return self.layout_configuration.quantity_for_pickup(pickup)

    def set_quantity_for_pickup(self, pickup: PickupEntry, new_quantity: int) -> None:
        """Changes the quantities for one specific pickup."""
        quantities = self.layout_configuration.pickup_quantities.pickups_with_custom_quantities
        quantities[pickup] = new_quantity
        self.set_pickup_quantities(quantities)

    def set_pickup_quantities(self, quantities: Dict[PickupEntry, int]):
        """Changes the quantities for all pickups"""
        self._check_editable_and_mark_dirty()

        self._layout_configuration = dataclasses.replace(
            self.layout_configuration,
            pickup_quantities=self.layout_configuration.pickup_quantities.with_new_quantities(quantities))

    def _check_editable_and_mark_dirty(self):
        """Checks if _nested_autosave_level is not 0 and marks at least one value was changed."""
        assert self._nested_autosave_level != 0, "Attempting to edit an Options, but it wasn't made editable"
        self._is_dirty = True
