import copy
import dataclasses
import json
import uuid
from distutils.version import StrictVersion
from enum import Enum
from pathlib import Path
from typing import Optional, TypeVar, Callable, Any, Set, List, Dict

from randovania.game_connection.memory_executor_choice import MemoryExecutorChoice
from randovania.games.game import RandovaniaGame
from randovania.interface_common import persistence, update_checker
from randovania.interface_common.persisted_options import get_persisted_options_from_data, serialized_data_for_options
from randovania.layout import game_to_class
from randovania.layout.game_to_class import AnyCosmeticPatches

T = TypeVar("T")


def identity(v: T) -> T:
    return v


class InfoAlert(Enum):
    FAQ = "faq"
    MULTI_ENERGY_ALERT = "multi-energy-alert"
    MULTIWORLD_FAQ = "multi-faq"
    NINTENDONT_UNSTABLE = "nintendont-unstable"


@dataclasses.dataclass(frozen=True)
class Serializer:
    encode: Callable[[Any], Any]
    decode: Callable[[Any], Any]


def serialize_alerts(alerts: Set[InfoAlert]) -> List[str]:
    return sorted(a.value for a in alerts)


def decode_alerts(data: List[str]):
    result = set()
    for item in data:
        try:
            result.add(InfoAlert(item))
        except ValueError:
            continue

    return result


def decode_if_not_none(value, decoder):
    if value is not None:
        return decoder(value)
    else:
        return None


@dataclasses.dataclass(frozen=True)
class PerGameOptions:
    cosmetic_patches: AnyCosmeticPatches
    input_path: Optional[Path] = None
    output_directory: Optional[Path] = None
    output_format: Optional[str] = None

    @property
    def as_json(self):
        return {
            "cosmetic_patches": self.cosmetic_patches.as_json,
            "input_path": str(self.input_path) if self.input_path is not None else None,
            "output_directory": str(self.output_directory) if self.output_directory is not None else None,
            "output_format": self.output_format if self.output_format is not None else None,
        }

    @classmethod
    def default_for_game(cls, game: RandovaniaGame) -> "PerGameOptions":
        return cls(cosmetic_patches=game_to_class.GAME_TO_COSMETIC[game]())

    @classmethod
    def from_json(cls, value, game: RandovaniaGame) -> "PerGameOptions":
        cosmetic_patches = game_to_class.GAME_TO_COSMETIC[game].from_json(value["cosmetic_patches"])
        return PerGameOptions(
            cosmetic_patches=cosmetic_patches,
            input_path=decode_if_not_none(value["input_path"], Path),
            output_format=value["output_format"],
            output_directory=decode_if_not_none(value["output_directory"], Path),
        )


def serialize_per_game_dict(val: Dict[RandovaniaGame, PerGameOptions]) -> dict:
    return {
        key.value: value.as_json
        for key, value in val.items()
    }


def decode_per_game_dict(val: dict) -> Dict[RandovaniaGame, PerGameOptions]:
    return {
        RandovaniaGame(key): PerGameOptions.from_json(value, game=RandovaniaGame(key))
        for key, value in val.items()
    }


_SERIALIZER_FOR_FIELD = {
    "last_changelog_displayed": Serializer(identity, str),
    "advanced_validate_seed_after": Serializer(identity, bool),
    "advanced_timeout_during_generation": Serializer(identity, bool),
    "auto_save_spoiler": Serializer(identity, bool),
    "dark_mode": Serializer(identity, bool),
    "experimental_games": Serializer(identity, bool),
    "selected_preset_uuid": Serializer(str, uuid.UUID),
    "per_game_options": Serializer(serialize_per_game_dict, decode_per_game_dict),
    "displayed_alerts": Serializer(serialize_alerts, decode_alerts),
    "game_backend": Serializer(lambda it: it.value, MemoryExecutorChoice),
    "nintendont_ip": Serializer(identity, str),
    "selected_tracker": Serializer(identity, str),
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
    _user_dir: Path
    _on_options_changed: Optional[Callable[[], None]] = None
    _nested_autosave_level: int = 0
    _is_dirty: bool = False

    _last_changelog_displayed: str
    _advanced_validate_seed_after: Optional[bool] = None
    _advanced_timeout_during_generation: Optional[bool] = None
    _auto_save_spoiler: Optional[bool] = None
    _dark_mode: Optional[bool] = None
    _experimental_games: Optional[bool] = None
    _selected_preset_uuid: Optional[uuid.UUID] = None
    _per_game_options: Optional[Dict[RandovaniaGame, PerGameOptions]] = None
    _displayed_alerts: Optional[Set[InfoAlert]] = None
    _game_backend: Optional[MemoryExecutorChoice] = None
    _nintendont_ip: Optional[str] = None
    _selected_tracker: Optional[str] = None

    def __init__(self, data_dir: Path, user_dir: Optional[Path] = None):
        self._data_dir = data_dir
        self._user_dir = user_dir or data_dir
        self._last_changelog_displayed = str(update_checker.strict_current_version())

    @classmethod
    def with_default_data_dir(cls) -> "Options":
        return cls(persistence.local_data_dir(), persistence.roaming_data_dir())

    def _read_persisted_options(self) -> Optional[dict]:
        try:
            contents = self._data_dir.joinpath("config.json").read_text("utf-8")
            if contents.strip() == "":
                return None
            return json.loads(contents)
        except FileNotFoundError:
            return None

    def _set_field(self, field_name: str, value):
        setattr(self, "_" + field_name, value)

    def load_from_disk(self, ignore_decode_errors: bool = False) -> bool:
        """
        Loads the file created with `_save_to_disk`.
        :param ignore_decode_errors: If True, errors in the config file are ignored.
        :return: True, if a valid file exists.
        """
        try:
            persisted_data = self._read_persisted_options()

        except json.decoder.JSONDecodeError as e:
            if ignore_decode_errors:
                persisted_data = None
            else:
                raise DecodeFailedException(f"Unable to decode JSON: {e}")

        if persisted_data is None:
            return False

        persisted_options = get_persisted_options_from_data(persisted_data)
        self.load_from_persisted(persisted_options, ignore_decode_errors)
        return True

    def load_from_persisted(self,
                            persisted: dict,
                            ignore_decode_errors: bool,
                            ):
        """
        Loads fields from the given persisted options.
        :param persisted:
        :param ignore_decode_errors:
        :return:
        """
        for field_name, serializer in _SERIALIZER_FOR_FIELD.items():
            value = persisted.get(field_name, None)
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

        # Write to a separate file, so we don't corrupt the existing one in case we unexpectedly
        # are unable to finish writing the file
        new_config_path = self._data_dir.joinpath("config_new.json")
        with new_config_path.open("w") as options_file:
            json.dump(data_to_persist, options_file,
                      indent=4, separators=(',', ': '))

        # Place the new, complete, config to the desired path
        config_path = self._data_dir.joinpath("config.json")
        new_config_path.replace(config_path)

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
        self._auto_save_spoiler = None
        self._per_game_options = None
        self._displayed_alerts = None
        self._dark_mode = None
        self._experimental_games = None
        self._game_backend = None
        self._nintendont_ip = None
        self._selected_tracker = None

    # Files paths
    @property
    def internal_copies_path(self) -> Path:
        return self._data_dir.joinpath("internal_copies")

    @property
    def tracker_files_path(self) -> Path:
        return self._data_dir.joinpath("tracker")

    @property
    def presets_path(self) -> Path:
        return self._user_dir.joinpath("presets")

    @property
    def game_history_path(self) -> Path:
        return self._data_dir.joinpath("game_history")

    @property
    def logs_path(self) -> Path:
        return self._data_dir.joinpath("logs")

    @property
    def data_dir(self) -> Path:
        return self._data_dir

    @property
    def user_dir(self) -> Path:
        return self._user_dir

    # Access to Direct fields
    @property
    def last_changelog_displayed(self) -> StrictVersion:
        return StrictVersion(self._last_changelog_displayed)

    @last_changelog_displayed.setter
    def last_changelog_displayed(self, value: StrictVersion):
        if value != self.last_changelog_displayed:
            self._check_editable_and_mark_dirty()
            self._last_changelog_displayed = str(value)

    @property
    def auto_save_spoiler(self) -> bool:
        return _return_with_default(self._auto_save_spoiler, lambda: False)

    @auto_save_spoiler.setter
    def auto_save_spoiler(self, value: bool):
        self._edit_field("auto_save_spoiler", value)

    @property
    def dark_mode(self) -> bool:
        return _return_with_default(self._dark_mode, lambda: False)

    @dark_mode.setter
    def dark_mode(self, value: bool):
        self._edit_field("dark_mode", value)

    @property
    def experimental_games(self) -> bool:
        return _return_with_default(self._experimental_games, lambda: False)

    @experimental_games.setter
    def experimental_games(self, value):
        self._edit_field("experimental_games", value)

    @property
    def selected_preset_uuid(self) -> Optional[uuid.UUID]:
        return self._selected_preset_uuid

    @selected_preset_uuid.setter
    def selected_preset_uuid(self, value: uuid.UUID):
        self._edit_field("selected_preset_uuid", value)

    @property
    def game_backend(self) -> MemoryExecutorChoice:
        return _return_with_default(self._game_backend, lambda: MemoryExecutorChoice.DOLPHIN)

    @game_backend.setter
    def game_backend(self, value: MemoryExecutorChoice):
        self._edit_field("game_backend", value)

    @property
    def nintendont_ip(self) -> Optional[str]:
        return self._nintendont_ip

    @nintendont_ip.setter
    def nintendont_ip(self, value: Optional[str]):
        self._edit_field("nintendont_ip", value)

    @property
    def selected_tracker(self) -> str:
        return self._selected_tracker

    @selected_tracker.setter
    def selected_tracker(self, value: str):
        self._edit_field("selected_tracker", value)

    @property
    def displayed_alerts(self):
        return _return_with_default(self._displayed_alerts, set)

    @displayed_alerts.setter
    def displayed_alerts(self, value):
        self._edit_field("displayed_alerts", value)

    def is_alert_displayed(self, value: InfoAlert):
        return value in self.displayed_alerts

    def mark_alert_as_displayed(self, value: InfoAlert):
        if value not in self.displayed_alerts:
            # Create a copy so we don't modify the existing field
            alerts = set(self.displayed_alerts)
            alerts.add(value)
            with self:
                self.displayed_alerts = alerts

    @property
    def per_game_options(self):
        return _return_with_default(self._per_game_options, lambda: {})

    @per_game_options.setter
    def per_game_options(self, value):
        self._edit_field("per_game_options", value)

    def options_for_game(self, game: RandovaniaGame) -> PerGameOptions:
        return self.per_game_options.get(game, PerGameOptions.default_for_game(game))

    def set_options_for_game(self, game: RandovaniaGame, per_game: PerGameOptions):
        per_game_options = copy.copy(self.per_game_options)
        per_game_options[game] = per_game
        self.per_game_options = per_game_options

    # Advanced

    @property
    def advanced_validate_seed_after(self) -> bool:
        return _return_with_default(self._advanced_validate_seed_after, lambda: True)

    @advanced_validate_seed_after.setter
    def advanced_validate_seed_after(self, value: bool):
        self._edit_field("advanced_validate_seed_after", value)

    @property
    def advanced_timeout_during_generation(self) -> bool:
        return _return_with_default(self._advanced_timeout_during_generation, lambda: True)

    @advanced_timeout_during_generation.setter
    def advanced_timeout_during_generation(self, value: bool):
        self._edit_field("advanced_timeout_during_generation", value)

    ######

    def _check_editable_and_mark_dirty(self):
        """Checks if _nested_autosave_level is not 0 and marks at least one value was changed."""
        assert self._nested_autosave_level != 0, "Attempting to edit an Options, but it wasn't made editable"
        self._is_dirty = True

    def _edit_field(self, field_name: str, new_value):
        current_value = getattr(self, field_name)
        if current_value != new_value:
            self._check_editable_and_mark_dirty()
            self._set_field(field_name, new_value)
