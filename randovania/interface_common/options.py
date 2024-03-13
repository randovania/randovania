from __future__ import annotations

import dataclasses
import json
import uuid
from distutils.version import StrictVersion
from enum import Enum
from typing import TYPE_CHECKING, Any, TypeVar

from randovania.game_connection.builder.connector_builder_option import ConnectorBuilderOption
from randovania.games.game import RandovaniaGame
from randovania.interface_common import persisted_options, update_checker
from randovania.lib import migration_lib

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches

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


def serialize_alerts(alerts: set[InfoAlert]) -> list[str]:
    return sorted(a.value for a in alerts)


def decode_alerts(data: list[str]):
    result = set()
    for item in data:
        try:
            result.add(InfoAlert(item))
        except ValueError:
            continue

    return result


def serialize_uuid_set(elements: set[uuid.UUID]) -> list[str]:
    return sorted(str(a) for a in elements)


def serialize_uuid_list(elements: list[uuid.UUID]) -> list[str]:
    return [str(a) for a in elements]


def decode_uuid_container(data: list[str], add_item: Callable[[uuid.UUID], None]) -> None:
    for item in data:
        try:
            add_item(uuid.UUID(item))
        except ValueError:
            continue


def decode_uuid_set(data: list[str]) -> set[uuid.UUID]:
    result = set()
    decode_uuid_container(data, result.add)
    return result


def decode_uuid_list(data: list[str]) -> list[uuid.UUID]:
    result = []
    decode_uuid_container(data, result.append)
    return result


def serialize_uuid_dict(elements: dict[uuid.UUID, uuid.UUID]) -> dict[str, str]:
    return {str(key): str(value) for key, value in elements.items()}


def decode_uuid_dict(data: dict[str, str]) -> dict[uuid.UUID, uuid.UUID]:
    result = {}
    for key, value in data.items():
        try:
            result[uuid.UUID(key)] = uuid.UUID(value)
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
    cosmetic_patches: BaseCosmeticPatches

    @property
    def as_json(self):
        return {
            "cosmetic_patches": self.cosmetic_patches.as_json,
        }

    @classmethod
    def default_for_game(cls, game: RandovaniaGame) -> PerGameOptions:
        return cls(cosmetic_patches=game.data.layout.cosmetic_patches())

    @classmethod
    def from_json(cls, value: dict) -> PerGameOptions:
        raise NotImplementedError


_SERIALIZER_FOR_FIELD = {
    "last_changelog_displayed": Serializer(identity, str),
    "advanced_validate_seed_after": Serializer(identity, bool),
    "advanced_timeout_during_generation": Serializer(identity, bool),
    "advanced_generate_in_another_process": Serializer(identity, bool),
    "auto_save_spoiler": Serializer(identity, bool),
    "dark_mode": Serializer(identity, bool),
    "show_multiworld_banner": Serializer(identity, bool),
    "experimental_settings": Serializer(identity, bool),
    "allow_crash_reporting": Serializer(identity, bool),
    "use_user_for_crash_reporting": Serializer(identity, bool),
    "displayed_alerts": Serializer(serialize_alerts, decode_alerts),
    "hidden_preset_uuids": Serializer(serialize_uuid_set, decode_uuid_set),
    "tracker_default_game": Serializer(
        lambda it: it.value if it is not None else None, lambda it: RandovaniaGame(it) if it is not None else None
    ),
    "parent_for_presets": Serializer(serialize_uuid_dict, decode_uuid_dict),
    "connector_builders": Serializer(
        lambda obj: [it.as_json for it in obj], lambda obj: [ConnectorBuilderOption.from_json(it) for it in obj]
    ),
}

_PER_GAME_SERIALIZERS = {
    "is_game_expanded": Serializer(identity, bool),
    "selected_preset_uuid": Serializer(str, uuid.UUID),
    "selected_tracker": Serializer(identity, str),
    "preset_order": Serializer(serialize_uuid_list, decode_uuid_list),
}


def add_per_game_serializer():
    def make_decoder(g: RandovaniaGame):
        return lambda it: g.options.from_json(it)

    for game in RandovaniaGame.all_games():
        _SERIALIZER_FOR_FIELD[f"game_{game.value}"] = Serializer(
            lambda it: it.as_json,
            make_decoder(game),
        )
        for key, serializer in _PER_GAME_SERIALIZERS.items():
            _SERIALIZER_FOR_FIELD[f"{key}_{game.value}"] = serializer


add_per_game_serializer()


def _return_with_default(value: T | None, default_factory: Callable[[], T]) -> T:
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
    _on_options_changed: Callable[[], None] | None = None
    _nested_autosave_level: int = 0
    _is_dirty: bool = False

    _last_changelog_displayed: str
    _advanced_validate_seed_after: bool | None = None
    _advanced_timeout_during_generation: bool | None = None
    _advanced_generate_in_another_process: bool | None = None
    _auto_save_spoiler: bool | None = None
    _dark_mode: bool | None = None
    _show_multiworld_banner: bool | None = None
    _experimental_settings: bool | None = None
    _allow_crash_reporting: bool | None = None
    _use_user_for_crash_reporting: bool | None = None
    _displayed_alerts: set[InfoAlert] | None = None
    _hidden_preset_uuids: set[uuid.UUID] | None = None
    _parent_for_presets: dict[uuid.UUID, uuid.UUID] | None = None
    _tracker_default_game: RandovaniaGame | None = None
    _connector_builders: list[ConnectorBuilderOption] | None = None

    def __init__(self, data_dir: Path, user_dir: Path | None = None):
        self._data_dir = data_dir
        self._user_dir = user_dir or data_dir
        self._last_changelog_displayed = str(update_checker.strict_current_version())

        for game in RandovaniaGame.all_games():
            self._set_field(f"game_{game.value}", None)
            for key in _PER_GAME_SERIALIZERS.keys():
                self._set_field(f"{key}_{game.value}", None)

    def __getattr__(self, item):
        if isinstance(item, str):
            game_name = None
            if item.startswith("game_"):
                game_name = item[len("game_") :]
            else:
                for key in _PER_GAME_SERIALIZERS.keys():
                    field_name = f"{key}_"
                    if item.startswith(field_name):
                        game_name = item[len(field_name) :]
                        break
            if game_name is None:
                raise AttributeError(item)

            try:
                game: RandovaniaGame = RandovaniaGame(game_name)
            except ValueError:
                raise AttributeError(item)

            result = getattr(self, f"_{item}", None)
            if result is None:
                if item.startswith("game_"):
                    result = game.options.default_for_game(game)
                elif item.startswith("is_game_expanded_"):
                    result = game.data.development_state.is_stable
            return result

        raise AttributeError(item)

    def _set_field(self, field_name: str, value):
        setattr(self, "_" + field_name, value)

    def load_from_disk(self, ignore_decode_errors: bool = False) -> bool:
        """
        Loads the file created with `_save_to_disk`.
        :param ignore_decode_errors: If True, errors in the config file are ignored.
        :return: True, if a valid file exists.
        """
        result = None
        for content in persisted_options.find_config_files(self._data_dir):
            try:
                persisted_data = json.loads(content)
                result = persisted_options.get_persisted_options_from_data(persisted_data)

            except (json.decoder.JSONDecodeError, migration_lib.UnsupportedVersion) as e:
                if ignore_decode_errors:
                    continue
                else:
                    if isinstance(e, migration_lib.UnsupportedVersion):
                        raise DecodeFailedException(f"Configuration file unsupported: {e}")
                    else:
                        raise DecodeFailedException(f"Unable to decode JSON: {e}")

            # Read something successfully, so stop it here
            break

        if result is None:
            return False

        self.load_from_persisted(result, ignore_decode_errors)
        return True

    def load_from_persisted(
        self,
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
                        raise DecodeFailedException(f"Unable to decode field {field_name}: {err}")

                if decoded is not None:
                    self._set_field(field_name, decoded)

    def _serialize_fields(self) -> dict:
        data_to_persist = {}
        for field_name, serializer in _SERIALIZER_FOR_FIELD.items():
            value = getattr(self, "_" + field_name, None)
            if value is not None:
                data_to_persist[field_name] = serializer.encode(value)

        return persisted_options.serialized_data_for_options(data_to_persist)

    def _save_to_disk(self):
        """Serializes the fields of this Option and writes then to a file."""
        self._is_dirty = False
        data_to_persist = self._serialize_fields()
        persisted_options.replace_config_file_with(self._data_dir, data_to_persist)

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
        for field_name in _SERIALIZER_FOR_FIELD.keys():
            if field_name == "last_changelog_displayed":
                continue
            self._set_field(field_name, None)

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
    def show_multiworld_banner(self) -> bool:
        return _return_with_default(self._show_multiworld_banner, lambda: False)

    @show_multiworld_banner.setter
    def show_multiworld_banner(self, value: bool) -> None:
        self._edit_field("show_multiworld_banner", value)

    @property
    def experimental_settings(self) -> bool:
        return _return_with_default(self._experimental_settings, lambda: False)

    @experimental_settings.setter
    def experimental_settings(self, value: bool):
        self._edit_field("experimental_settings", value)

    @property
    def allow_crash_reporting(self) -> bool:
        return _return_with_default(self._allow_crash_reporting, lambda: True)

    @allow_crash_reporting.setter
    def allow_crash_reporting(self, value: bool):
        self._edit_field("allow_crash_reporting", value)

    @property
    def use_user_for_crash_reporting(self) -> bool:
        return _return_with_default(self._use_user_for_crash_reporting, lambda: True)

    @use_user_for_crash_reporting.setter
    def use_user_for_crash_reporting(self, value):
        self._edit_field("use_user_for_crash_reporting", value)

    @property
    def tracker_default_game(self) -> RandovaniaGame | None:
        return self._tracker_default_game

    @tracker_default_game.setter
    def tracker_default_game(self, value: RandovaniaGame | None):
        self._edit_field("tracker_default_game", value)

    def selected_tracker_for(self, game: RandovaniaGame) -> str:
        return getattr(self, f"selected_tracker_{game.value}")

    def set_selected_tracker_for(self, game: RandovaniaGame, value: str):
        self._edit_field(f"selected_tracker_{game.value}", value)

    @property
    def connector_builders(self) -> list[ConnectorBuilderOption]:
        return self._connector_builders or []

    @connector_builders.setter
    def connector_builders(self, value: list[ConnectorBuilderOption]):
        self._edit_field("connector_builders", value)

    @property
    def displayed_alerts(self) -> set[InfoAlert]:
        return _return_with_default(self._displayed_alerts, set)

    @displayed_alerts.setter
    def displayed_alerts(self, value: set[InfoAlert]):
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

    # Per Game

    def options_for_game(self, game: RandovaniaGame) -> PerGameOptions:
        return getattr(self, f"game_{game.value}")

    def set_options_for_game(self, game: RandovaniaGame, per_game: PerGameOptions):
        if type(per_game) != game.options:
            raise ValueError(f"Expected {game.options}, got {type(per_game)}")

        self._edit_field(f"game_{game.value}", per_game)

    def is_game_expanded(self, game: RandovaniaGame) -> bool:
        return getattr(self, f"is_game_expanded_{game.value}")

    def set_is_game_expanded(self, game: RandovaniaGame, value: bool):
        self._edit_field(f"is_game_expanded_{game.value}", value)

    def selected_preset_uuid_for(self, game: RandovaniaGame) -> uuid.UUID | None:
        return getattr(self, f"selected_preset_uuid_{game.value}")

    def set_selected_preset_uuid_for(self, game: RandovaniaGame, value: uuid.UUID | None):
        self._edit_field(f"selected_preset_uuid_{game.value}", value)

    @property
    def hidden_preset_uuids(self):
        return _return_with_default(self._hidden_preset_uuids, set)

    @hidden_preset_uuids.setter
    def hidden_preset_uuids(self, value):
        self._edit_field("hidden_preset_uuids", value)

    def get_preset_order_for(self, game: RandovaniaGame) -> list[uuid.UUID]:
        return list(_return_with_default(getattr(self, f"preset_order_{game.value}"), list))

    def set_preset_order_for(self, game: RandovaniaGame, value: list[uuid.UUID]):
        self._edit_field(f"preset_order_{game.value}", value)

    def is_preset_uuid_hidden(self, the_uuid: uuid.UUID) -> bool:
        return the_uuid in self.hidden_preset_uuids

    def set_preset_uuid_hidden(self, the_uuid: uuid.UUID, value: bool):
        is_present = the_uuid in self.hidden_preset_uuids

        if is_present != value:
            # Create a copy, so we don't modify the existing field
            uuids = set(self.hidden_preset_uuids)
            if value:
                uuids.add(the_uuid)
            else:
                uuids.remove(the_uuid)
            with self:
                self.hidden_preset_uuids = uuids

    @property
    def parent_for_presets(self) -> dict[uuid.UUID, uuid.UUID]:
        return _return_with_default(self._parent_for_presets, dict)

    @parent_for_presets.setter
    def parent_for_presets(self, value: dict[uuid.UUID, uuid.UUID]):
        self._edit_field("parent_for_presets", value)

    def get_parent_for_preset(self, preset: uuid.UUID) -> uuid.UUID | None:
        return self.parent_for_presets.get(preset)

    def set_parent_for_preset(self, preset: uuid.UUID, parent: uuid.UUID | None):
        current_dict = self.parent_for_presets

        if current_dict.get(preset) != parent:
            # Create a copy, so we don't modify the existing field
            new_dict = dict(current_dict)
            if parent is None:
                new_dict.pop(preset)
            else:
                new_dict[preset] = parent
            with self:
                self.parent_for_presets = new_dict

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

    @property
    def advanced_generate_in_another_process(self) -> bool:
        return _return_with_default(self._advanced_generate_in_another_process, lambda: True)

    @advanced_generate_in_another_process.setter
    def advanced_generate_in_another_process(self, value: bool):
        self._edit_field("advanced_generate_in_another_process", value)

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
