import json
import math
import os
from collections import OrderedDict
from enum import IntEnum
from typing import List, Dict, Any, Set, Iterable, Optional

import py
from appdirs import AppDirs

from randovania.games.prime import binary_data
from randovania.resolver.data_reader import read_resource_database
from randovania.resolver.resources import SimpleResourceInfo

dirs = AppDirs("Randovania", False)


class CpuUsage(IntEnum):
    FULL = 1
    HIGH = 2
    BALANCED = 3
    MINIMAL = 4

    def num_cpu_for_count(self: "CpuUsage", cpu_count: int) -> int:
        if self == CpuUsage.FULL:
            result = cpu_count
        elif self == CpuUsage.HIGH:
            result = cpu_count - 1
        elif self == CpuUsage.BALANCED:
            result = math.floor(cpu_count / 2)
        elif self == CpuUsage.MINIMAL:
            result = 1
        else:
            raise ValueError("Unknown CpuUsage: {}".format(self))
        return max(1, min(result, cpu_count))


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
    def minimum_difficulty(self) -> int:
        return self.raw_data["min_difficulty"]

    @minimum_difficulty.setter
    def minimum_difficulty(self, value: int):
        validate_min_difficulty(value, self.raw_data)
        self.raw_data["min_difficulty"] = value

    @property
    def maximum_difficulty(self) -> int:
        return self.raw_data["max_difficulty"]

    @maximum_difficulty.setter
    def maximum_difficulty(self, value: int):
        validate_max_difficulty(value, self.raw_data)
        self.raw_data["max_difficulty"] = value

    @property
    def remove_item_loss(self) -> bool:
        return not self.raw_data["item_loss_enabled"]

    @remove_item_loss.setter
    def remove_item_loss(self, value: bool):
        self.raw_data["item_loss_enabled"] = not value

    @property
    def randomize_elevators(self) -> bool:
        return self.raw_data["randomize_elevators"]

    @randomize_elevators.setter
    def randomize_elevators(self, value: bool):
        self.raw_data["randomize_elevators"] = value

    @property
    def hud_memo_popup_removal(self) -> bool:
        return self.raw_data["hud_memo_popup_removal"]

    @hud_memo_popup_removal.setter
    def hud_memo_popup_removal(self, value: bool):
        self.raw_data["hud_memo_popup_removal"] = value

    @property
    def excluded_pickups(self) -> Set[int]:
        return set(self.raw_data["excluded_pickups"])

    @excluded_pickups.setter
    def excluded_pickups(self, value: Iterable[int]):
        self.raw_data["excluded_pickups"] = list(sorted(set(value)))

    @property
    def enabled_tricks(self) -> Set[int]:
        return set(self.raw_data["enabled_tricks"])

    @enabled_tricks.setter
    def enabled_tricks(self, value: Iterable[SimpleResourceInfo]):
        self.raw_data["enabled_tricks"] = list(sorted({
            trick.index
            for trick in value
        }))

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
    def cpu_usage(self) -> CpuUsage:
        return CpuUsage(self.raw_data["cpu_usage"])

    @cpu_usage.setter
    def cpu_usage(self, value: CpuUsage):
        self.raw_data["cpu_usage"] = value

    @property
    def advanced_options(self) -> bool:
        return self.raw_data["show_advanced_options"]

    @advanced_options.setter
    def advanced_options(self, value: bool):
        self.raw_data["show_advanced_options"] = value

    def __getitem__(self, item):
        return self.raw_data[item]

    def __setitem__(self, key, value):
        self.raw_data[key] = value

    def keys(self):
        return self.raw_data.keys()

    def items(self):
        return self.raw_data.items()


def _default_options() -> Dict[str, Any]:
    options: Dict[str, Any] = OrderedDict()
    options["max_difficulty"] = 3
    options["min_difficulty"] = 0
    options["item_loss_enabled"] = False
    options["enabled_tricks"] = [
        trick.index
        for trick in read_resource_database(binary_data.decode_default_prime2()["resource_database"]).trick
    ]
    options["excluded_pickups"] = []
    options["randomize_elevators"] = False
    options["hud_memo_popup_removal"] = True
    options["game_files_path"] = None
    options["cpu_usage"] = CpuUsage.FULL
    options["seed"] = 0
    options["show_advanced_options"] = False
    return options


def default_files_location() -> str:
    return os.path.join(dirs.user_data_dir, "extracted_game")


def value_parser_int(s: str) -> int:
    try:
        return int(s)
    except ValueError:
        raise ValueError("'{}' is not a number.".format(s)) from None


def value_parser_bool(s: str) -> bool:
    false_values = ("off", "false", "no", "0")
    true_values = ("on", "true", "yes", "1")
    s = s.lower()
    if s not in false_values and s not in true_values:
        raise ValueError("{} is not a boolean value.".format(s))
    return s in true_values


def value_parser_str(s: str) -> str:
    return s


def value_parser_int_array(s: str) -> List[int]:
    if s.lower() == "none":
        return []
    return [
        value_parser_int(x) for x in s.split()
    ]


value_parsers = {
    int: value_parser_int,
    bool: value_parser_bool,
    str: value_parser_str,
    list: value_parser_int_array,
}


def validate_difficulty(difficulty: int):
    if difficulty < 0:
        raise ValueError("Difficulty should be at least 0")
    if difficulty > MAX_DIFFICULTY:
        raise ValueError("Difficulty should be at most {}".format(MAX_DIFFICULTY))


def validate_min_difficulty(difficulty: int, current_options):
    validate_difficulty(difficulty)
    if difficulty > current_options["max_difficulty"]:
        raise ValueError("Min difficulty should be the same or smaller"
                         " than min difficulty ({})".format(current_options["min_difficulty"]))


def validate_max_difficulty(difficulty: int, current_options):
    validate_difficulty(difficulty)
    if difficulty < current_options["min_difficulty"]:
        raise ValueError("Max difficulty should be the same or higher"
                         " than min difficulty ({})".format(current_options["min_difficulty"]))


def validate_pickup_list(pickup_list: List[int], current_options):
    pass


def validate_iso_path(iso_path: str, options):
    try:
        with open(iso_path, "rb"):
            pass
    except FileNotFoundError as x:
        raise ValueError(str(x))

    if not iso_path.lower().endswith(".iso"):
        raise ValueError("Does not end in '.iso'")


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


options_validation = {
    "max_difficulty": validate_max_difficulty,
    "min_difficulty": validate_min_difficulty,
    "excluded_pickups": validate_pickup_list,
    "iso_path": validate_iso_path,
}
MAX_DIFFICULTY = 5
