import dataclasses
import json
from distutils.version import StrictVersion
from pathlib import Path
from typing import Optional, TypeVar, Callable, Any

import randovania
from randovania.interface_common import persistence
from randovania.interface_common.cosmetic_patches import CosmeticPatches
from randovania.interface_common.persisted_options import get_persisted_options_from_data, serialized_data_for_options
from randovania.layout.ammo_configuration import AmmoConfiguration
from randovania.layout.layout_configuration import LayoutConfiguration, LayoutElevators, LayoutTrickLevel, \
    LayoutSkyTempleKeyMode
from randovania.layout.major_items_configuration import MajorItemsConfiguration
from randovania.layout.patcher_configuration import PatcherConfiguration
from randovania.layout.permalink import Permalink

T = TypeVar("T")


def identity(v: T) -> T:
    return v


@dataclasses.dataclass(frozen=True)
class Serializer:
    encode: Callable[[Any], Any]
    decode: Callable[[Any], Any]


_SERIALIZER_FOR_FIELD = {
    "last_changelog_displayed": Serializer(identity, str),
    "advanced_validate_seed_after": Serializer(identity, bool),
    "advanced_timeout_during_generation": Serializer(identity, bool),
    "create_spoiler": Serializer(identity, bool),
    "output_directory": Serializer(str, Path),
    "patcher_configuration": Serializer(lambda p: p.as_json, PatcherConfiguration.from_json_dict),
    "layout_configuration": Serializer(lambda p: p.as_json, LayoutConfiguration.from_json_dict),
    "cosmetic_patches": Serializer(lambda p: p.as_json, CosmeticPatches.from_json_dict),
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


class DecodeFailedException(ValueError):
    pass


class Options:
    _data_dir: Path
    _on_options_changed: Optional[Callable[[], None]] = None
    _nested_autosave_level: int = 0
    _is_dirty: bool = False

    _last_changelog_displayed: str
    _advanced_validate_seed_after: Optional[bool] = None
    _advanced_timeout_during_generation: Optional[bool] = None
    _seed_number: Optional[int] = None
    _create_spoiler: Optional[bool] = None
    _output_directory: Optional[Path] = None
    _patcher_configuration: Optional[PatcherConfiguration] = None
    _layout_configuration: Optional[LayoutConfiguration] = None
    _cosmetic_patches: Optional[CosmeticPatches] = None

    def __init__(self, data_dir: Path):
        self._data_dir = data_dir
        self._last_changelog_displayed = randovania.VERSION

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

    def load_from_disk(self, ignore_decode_errors: bool = False):
        persisted_data = self._read_persisted_options()
        if persisted_data is None:
            return

        persisted_options = get_persisted_options_from_data(persisted_data)
        for field_name, serializer in _SERIALIZER_FOR_FIELD.items():
            value = persisted_options.get(field_name, None)
            if value is not None:
                try:
                    decoded = serializer.decode(value)
                except Exception as err:
                    if ignore_decode_errors:
                        decoded = None
                    else:
                        raise DecodeFailedException(
                            f"Unable to decode field {field_name}: {err}"
                        )

                if decoded is not None:
                    self._set_field(field_name, decoded)

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
        self._advanced_validate_seed_after = None
        self._advanced_timeout_during_generation = None
        self._create_spoiler = None
        self._patcher_configuration = None
        self._layout_configuration = None
        self._cosmetic_patches = None

    # Files paths
    @property
    def backup_files_path(self) -> Path:
        return self._data_dir.joinpath("backup")

    @property
    def game_files_path(self) -> Path:
        return self._data_dir.joinpath("extracted_game")

    # Access to Direct fields
    @property
    def last_changelog_displayed(self) -> StrictVersion:
        return StrictVersion(self._last_changelog_displayed)

    @last_changelog_displayed.setter
    def last_changelog_displayed(self, value: StrictVersion):
        self._check_editable_and_mark_dirty()
        self._last_changelog_displayed = str(value)

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

    @property
    def cosmetic_patches(self) -> CosmeticPatches:
        return _return_with_default(self._cosmetic_patches, CosmeticPatches.default)

    # Advanced

    @property
    def advanced_validate_seed_after(self) -> bool:
        return _return_with_default(self._advanced_validate_seed_after, lambda: True)

    @advanced_validate_seed_after.setter
    def advanced_validate_seed_after(self, value: bool):
        self._check_editable_and_mark_dirty()
        self._advanced_validate_seed_after = value

    @property
    def advanced_timeout_during_generation(self) -> bool:
        return _return_with_default(self._advanced_timeout_during_generation, lambda: True)

    @advanced_timeout_during_generation.setter
    def advanced_timeout_during_generation(self, value: bool):
        self._check_editable_and_mark_dirty()
        self._advanced_timeout_during_generation = value

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
    def include_menu_mod(self) -> bool:
        return self.patcher_configuration.menu_mod

    @include_menu_mod.setter
    def include_menu_mod(self, value: bool):
        self.set_patcher_configuration_field("menu_mod", value)

    @property
    def warp_to_start(self) -> bool:
        return self.patcher_configuration.warp_to_start

    @warp_to_start.setter
    def warp_to_start(self, value: bool):
        self.set_patcher_configuration_field("warp_to_start", value)

    @property
    def pickup_model_style(self):
        return self.patcher_configuration.pickup_model_style

    @pickup_model_style.setter
    def pickup_model_style(self, value):
        self.set_patcher_configuration_field("pickup_model_style", value)

    @property
    def pickup_model_data_source(self):
        return self.patcher_configuration.pickup_model_data_source

    @pickup_model_data_source.setter
    def pickup_model_data_source(self, value):
        self.set_patcher_configuration_field("pickup_model_data_source", value)

    def set_patcher_configuration_field(self, field_name: str, value):
        current_configuration = self.patcher_configuration
        new_configuration = dataclasses.replace(current_configuration, **{field_name: value})
        if current_configuration != new_configuration:
            self._check_editable_and_mark_dirty()
            self._patcher_configuration = new_configuration

    # Access to fields inside CosmeticPatches
    @property
    def hud_memo_popup_removal(self) -> bool:
        return self.cosmetic_patches.disable_hud_popup

    @hud_memo_popup_removal.setter
    def hud_memo_popup_removal(self, value: bool):
        self._check_editable_and_mark_dirty()
        self._cosmetic_patches = dataclasses.replace(self.cosmetic_patches, disable_hud_popup=value)

    @property
    def speed_up_credits(self) -> bool:
        return self.cosmetic_patches.speed_up_credits

    @speed_up_credits.setter
    def speed_up_credits(self, value: bool):
        self._check_editable_and_mark_dirty()
        self._cosmetic_patches = dataclasses.replace(self.cosmetic_patches, speed_up_credits=value)

    @property
    def open_map(self) -> bool:
        return self.cosmetic_patches.open_map

    @open_map.setter
    def open_map(self, value: bool):
        self._check_editable_and_mark_dirty()
        self._cosmetic_patches = dataclasses.replace(self.cosmetic_patches, open_map=value)

    @property
    def pickup_markers(self) -> bool:
        return self.cosmetic_patches.pickup_markers

    @pickup_markers.setter
    def pickup_markers(self, value: bool):
        self._check_editable_and_mark_dirty()
        self._cosmetic_patches = dataclasses.replace(self.cosmetic_patches, pickup_markers=value)

    # Access to fields inside LayoutConfiguration

    @property
    def layout_configuration_trick_level(self) -> LayoutTrickLevel:
        return self.layout_configuration.trick_level

    @layout_configuration_trick_level.setter
    def layout_configuration_trick_level(self, value: LayoutTrickLevel):
        self.set_layout_configuration_field("trick_level", value)

    @property
    def layout_configuration_sky_temple_keys(self) -> LayoutSkyTempleKeyMode:
        return self.layout_configuration.sky_temple_keys

    @layout_configuration_sky_temple_keys.setter
    def layout_configuration_sky_temple_keys(self, value: LayoutSkyTempleKeyMode):
        self.set_layout_configuration_field("sky_temple_keys", value)

    @property
    def layout_configuration_elevators(self) -> LayoutElevators:
        return self.layout_configuration.elevators

    @layout_configuration_elevators.setter
    def layout_configuration_elevators(self, value: LayoutElevators):
        self.set_layout_configuration_field("elevators", value)

    @property
    def major_items_configuration(self) -> MajorItemsConfiguration:
        return self.layout_configuration.major_items_configuration

    @major_items_configuration.setter
    def major_items_configuration(self, value: MajorItemsConfiguration):
        self.set_layout_configuration_field("major_items_configuration", value)

    @property
    def ammo_configuration(self) -> AmmoConfiguration:
        return self.layout_configuration.ammo_configuration

    @ammo_configuration.setter
    def ammo_configuration(self, value: AmmoConfiguration):
        self.set_layout_configuration_field("ammo_configuration", value)

    def set_layout_configuration_field(self, field_name: str, value):
        current_layout = self.layout_configuration
        new_layout = dataclasses.replace(self.layout_configuration, **{field_name: value})
        if current_layout != new_layout:
            self._check_editable_and_mark_dirty()
            self._layout_configuration = new_layout

    ######

    def _check_editable_and_mark_dirty(self):
        """Checks if _nested_autosave_level is not 0 and marks at least one value was changed."""
        assert self._nested_autosave_level != 0, "Attempting to edit an Options, but it wasn't made editable"
        self._is_dirty = True
