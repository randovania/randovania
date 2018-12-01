import json
import os
from collections import OrderedDict
from pathlib import Path
from typing import Dict, Any, Optional

from randovania.interface_common import persistence
from randovania.resolver.layout_configuration import LayoutConfiguration, LayoutRandomizedFlag, LayoutEnabledFlag, \
    LayoutDifficulty, LayoutTrickLevel, LayoutMode


def _convert_logic(new_options: dict):
    trick_level = new_options.pop("layout_logic")
    if trick_level == "no-glitches":
        trick_level = "no-tricks"
    new_options["layout_trick_level"] = trick_level


_FIELDS_TO_MIGRATE = {
    "layout_logic": _convert_logic
}


class Options:
    def __init__(self, data_dir: Path):
        self.raw_data = _default_options()
        self._data_dir = data_dir

    @classmethod
    def with_default_data_dir(cls) -> "Options":
        return cls(persistence.user_data_dir())

    def load_from_disk(self):
        try:
            with self._data_dir.joinpath("config.json").open() as options_file:
                new_options = json.load(options_file)["options"]

            for old_option_name, converter in _FIELDS_TO_MIGRATE.items():
                if old_option_name in new_options:
                    converter(new_options)

            for option_name in self.raw_data.keys():
                if option_name in new_options:
                    self.raw_data[option_name] = new_options[option_name]

        except FileNotFoundError:
            pass

    def save_to_disk(self):
        self._data_dir.mkdir(parents=True, exist_ok=True)
        with self._data_dir.joinpath("config.json").open("w") as options_file:
            json.dump({
                "version": 1,
                "options": self.raw_data
            }, options_file)

    @property
    def hud_memo_popup_removal(self) -> bool:
        return self.raw_data["hud_memo_popup_removal"]

    @hud_memo_popup_removal.setter
    def hud_memo_popup_removal(self, value: bool):
        self.raw_data["hud_memo_popup_removal"] = value

    @property
    def include_menu_mod(self) -> bool:
        return self.raw_data["include_menu_mod"]

    @include_menu_mod.setter
    def include_menu_mod(self, value: bool):
        self.raw_data["include_menu_mod"] = value

    @property
    def backup_files_path(self) -> Path:
        return self._data_dir.joinpath("backup")

    @property
    def game_files_path(self) -> Path:
        result = self.raw_data["game_files_path"]
        if result is None:
            return default_files_location()
        return Path(result)

    @game_files_path.setter
    def game_files_path(self, value: Optional[Path]):
        self.raw_data["game_files_path"] = str(value)

    @property
    def advanced_options(self) -> bool:
        return self.raw_data["show_advanced_options"]

    @advanced_options.setter
    def advanced_options(self, value: bool):
        self.raw_data["show_advanced_options"] = value

    @property
    def display_generate_help(self) -> bool:
        return self.raw_data["display_generate_help"]

    @display_generate_help.setter
    def display_generate_help(self, value: bool):
        self.raw_data["display_generate_help"] = value

    @property
    def layout_configuration_trick_level(self) -> LayoutTrickLevel:
        # TODO: detect invalid values
        return LayoutTrickLevel(self.raw_data["layout_trick_level"])

    @layout_configuration_trick_level.setter
    def layout_configuration_trick_level(self, value: LayoutTrickLevel):
        self.raw_data["layout_logic"] = LayoutTrickLevel(value.value).value

    @property
    def layout_configuration_mode(self) -> LayoutMode:
        # TODO: detect invalid values
        return LayoutMode(self.raw_data["layout_mode"])

    @layout_configuration_mode.setter
    def layout_configuration_mode(self, value: LayoutMode):
        self.raw_data["layout_mode"] = LayoutMode(value.value).value

    @property
    def layout_configuration_sky_temple_keys(self) -> LayoutRandomizedFlag:
        # TODO: detect invalid values
        return LayoutRandomizedFlag(self.raw_data["layout_sky_temple_keys"])

    @layout_configuration_sky_temple_keys.setter
    def layout_configuration_sky_temple_keys(self, value: LayoutRandomizedFlag):
        self.raw_data["layout_sky_temple_keys"] = LayoutRandomizedFlag(value.value).value

    @property
    def layout_configuration_elevators(self) -> LayoutRandomizedFlag:
        # TODO: detect invalid values
        return LayoutRandomizedFlag(self.raw_data["layout_elevators"])

    @layout_configuration_elevators.setter
    def layout_configuration_elevators(self, value: LayoutRandomizedFlag):
        self.raw_data["layout_elevators"] = LayoutRandomizedFlag(value.value).value

    @property
    def layout_configuration_item_loss(self) -> LayoutEnabledFlag:
        # TODO: detect invalid values
        return LayoutEnabledFlag(self.raw_data["layout_item_loss"])

    @layout_configuration_item_loss.setter
    def layout_configuration_item_loss(self, value: LayoutEnabledFlag):
        self.raw_data["layout_item_loss"] = LayoutEnabledFlag(value.value).value

    def quantity_for_pickup(self, pickup_name: str) -> Optional[int]:
        return self.raw_data["quantity_for_pickup"].get(pickup_name)

    def set_quantity_for_pickup(self, pickup_name: str, new_quantity: Optional[int]) -> None:
        if new_quantity is not None:
            self.raw_data["quantity_for_pickup"][pickup_name] = new_quantity
        elif pickup_name in self.raw_data["quantity_for_pickup"]:
            del self.raw_data["quantity_for_pickup"][pickup_name]

    @property
    def layout_configuration(self) -> LayoutConfiguration:
        return LayoutConfiguration(
            trick_level=self.layout_configuration_trick_level,
            mode=self.layout_configuration_mode,
            sky_temple_keys=self.layout_configuration_sky_temple_keys,
            item_loss=self.layout_configuration_item_loss,
            elevators=self.layout_configuration_elevators,
            hundo_guaranteed=LayoutEnabledFlag.DISABLED,
            difficulty=LayoutDifficulty.NORMAL,
            pickup_quantities=self.raw_data["quantity_for_pickup"],
        )


def _default_options() -> Dict[str, Any]:
    options: Dict[str, Any] = OrderedDict()
    options["hud_memo_popup_removal"] = True
    options["game_files_path"] = None
    options["show_advanced_options"] = False
    options["display_generate_help"] = True
    options["include_menu_mod"] = False

    options["layout_trick_level"] = LayoutTrickLevel.NO_TRICKS.value
    options["layout_mode"] = LayoutMode.STANDARD.value
    options["layout_sky_temple_keys"] = LayoutRandomizedFlag.RANDOMIZED.value
    options["layout_elevators"] = LayoutRandomizedFlag.VANILLA.value
    options["layout_item_loss"] = LayoutEnabledFlag.ENABLED.value
    options["quantity_for_pickup"] = {}
    return options


def default_files_location() -> Path:
    return persistence.user_data_dir() / "extracted_game"


def validate_game_files_path(game_files_path: Path):
    if not game_files_path.is_dir():
        raise ValueError("Not a directory")

    required_files = ["default.dol", "FrontEnd.pak", "Metroid1.pak", "Metroid2.pak"]
    missing_files = [(game_files_path / required_file).is_file()
                     for required_file in required_files]

    if not all(missing_files):
        raise ValueError("Is not a valid game folder. Missing files: {}".format([
            filename for filename, exists in zip(required_files, missing_files)
            if not exists
        ]))


MAX_DIFFICULTY = 5
