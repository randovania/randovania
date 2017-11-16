import json
import os
from collections import OrderedDict
from typing import List, Dict, Any

import py


def default_options() -> Dict[str, Any]:
    options: Dict[str, Any] = OrderedDict()
    options["max_difficulty"] = 3
    options["min_difficulty"] = 0
    options["item_loss_enabled"] = False
    options["tricks_enabled"] = True
    options["excluded_pickups"] = []
    options["randomize_elevators"] = False
    options["hud_memo_popup_removal"] = True
    options["iso_path"] = ""
    options["game_files_path"] = ""
    options["seed"] = 0
    return options


def load_options_to(current_options):
    try:
        with open(os.path.expanduser("~/.config/randovania.json")) as options_file:
            new_options = json.load(options_file)["options"]

        for option_name in current_options.keys():
            if option_name in new_options:
                current_options[option_name] = new_options[option_name]

    except FileNotFoundError:
        pass


def save_options(options):
    config_folder = py.path.local(os.path.expanduser("~/.config"))
    config_folder.ensure_dir()
    with config_folder.join("randovania.json").open("w") as options_file:
        json.dump({
            "version": 1,
            "options": options
        }, options_file)


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


def validate_game_files_path(game_files_path: str, options):
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
    "game_files_path": validate_game_files_path,
}
MAX_DIFFICULTY = 5
