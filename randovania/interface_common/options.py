import json
import os
from collections import OrderedDict
from typing import Dict, Any, Optional

import py
from appdirs import AppDirs

from randovania.resolver.layout_configuration import LayoutConfiguration, LayoutRandomizedFlag, LayoutEnabledFlag, \
    LayoutDifficulty, LayoutLogic, LayoutMode

dirs = AppDirs("Randovania", False)


class Options:
    def __init__(self):
        self.raw_data = _default_options()

    def load_from_disk(self):
        try:
            with open(os.path.join(dirs.user_data_dir, "config.json")) as options_file:
                new_options = json.load(options_file)["options"]

            for option_name in self.raw_data.keys():
                if option_name in new_options:
                    self.raw_data[option_name] = new_options[option_name]

        except FileNotFoundError:
            pass

    def save_to_disk(self):
        config_folder = py.path.local(dirs.user_data_dir)
        config_folder.ensure_dir()
        with config_folder.join("config.json").open("w") as options_file:
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
    def game_files_path(self) -> str:
        result = self.raw_data["game_files_path"]
        if result is None:
            return default_files_location()
        return result

    @game_files_path.setter
    def game_files_path(self, value: Optional[str]):
        self.raw_data["game_files_path"] = value

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
    def layout_configuration_logic(self) -> LayoutLogic:
        # TODO: detect invalid values
        return LayoutLogic(self.raw_data["layout_logic"])

    @layout_configuration_logic.setter
    def layout_configuration_logic(self, value: LayoutLogic):
        self.raw_data["layout_logic"] = LayoutLogic(value.value).value

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
    def layout_configuration_item_loss(self) -> LayoutEnabledFlag:
        # TODO: detect invalid values
        return LayoutEnabledFlag(self.raw_data["layout_item_loss"])

    @layout_configuration_item_loss.setter
    def layout_configuration_item_loss(self, value: LayoutEnabledFlag):
        self.raw_data["layout_item_loss"] = LayoutEnabledFlag(value.value).value

    @property
    def layout_configuration(self) -> LayoutConfiguration:
        return LayoutConfiguration(
            logic=self.layout_configuration_logic,
            mode=self.layout_configuration_mode,
            sky_temple_keys=self.layout_configuration_sky_temple_keys,
            item_loss=self.layout_configuration_item_loss,
            elevators=LayoutRandomizedFlag.VANILLA,
            hundo_guaranteed=LayoutEnabledFlag.DISABLED,
            difficulty=LayoutDifficulty.NORMAL,
        )


def _default_options() -> Dict[str, Any]:
    options: Dict[str, Any] = OrderedDict()
    options["hud_memo_popup_removal"] = True
    options["game_files_path"] = None
    options["show_advanced_options"] = False
    options["display_generate_help"] = True

    options["layout_logic"] = LayoutLogic.NO_GLITCHES.value
    options["layout_mode"] = LayoutMode.STANDARD.value
    options["layout_sky_temple_keys"] = LayoutRandomizedFlag.RANDOMIZED.value
    options["layout_item_loss"] = LayoutEnabledFlag.ENABLED.value
    return options


def default_files_location() -> str:
    return os.path.join(dirs.user_data_dir, "extracted_game")


def validate_game_files_path(game_files_path: str):
    if not os.path.isdir(game_files_path):
        raise ValueError("Not a directory")

    required_files = ["default.dol", "FrontEnd.pak", "Metroid1.pak", "Metroid2.pak"]
    missing_files = [os.path.isfile(os.path.join(game_files_path, required_file))
                     for required_file in required_files]

    if not all(missing_files):
        raise ValueError("Is not a valid game folder. Missing files: {}".format([
            filename for filename, exists in zip(required_files, missing_files)
            if not exists
        ]))


MAX_DIFFICULTY = 5
