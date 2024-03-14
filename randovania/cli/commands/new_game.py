from __future__ import annotations

import dataclasses
import re
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from typing import TYPE_CHECKING

from frozendict import frozendict

from randovania.game_description import data_writer, default_database, pretty_print
from randovania.game_description.db.area import Area
from randovania.game_description.db.dock import DockRandoConfig, DockType, DockWeakness, DockWeaknessDatabase
from randovania.game_description.db.node import GenericNode
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.db.region import Region
from randovania.game_description.db.region_list import RegionList
from randovania.game_description.game_description import GameDescription
from randovania.game_description.pickup.pickup_category import PickupCategory
from randovania.game_description.pickup.pickup_database import PickupDatabase
from randovania.game_description.pickup.standard_pickup import StandardPickupDefinition
from randovania.game_description.requirements.base import Requirement
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.location_category import LocationCategory
from randovania.game_description.resources.resource_database import ResourceDatabase, default_base_damage_reduction
from randovania.games.game import RandovaniaGame
from randovania.layout.base.ammo_pickup_configuration import AmmoPickupConfiguration
from randovania.layout.base.base_configuration import StartingLocationList
from randovania.layout.base.dock_rando_configuration import DockRandoConfiguration, DockRandoMode, DockTypeState
from randovania.layout.base.standard_pickup_configuration import StandardPickupConfiguration
from randovania.layout.base.standard_pickup_state import StandardPickupState
from randovania.layout.versioned_preset import VersionedPreset
from randovania.lib import json_lib

if TYPE_CHECKING:
    from argparse import ArgumentParser

_GAMES_PATH = Path(__file__).parents[2].joinpath("games")

class_name_re = re.compile(r"\bBlank([A-Z][a-z])")
enum_name_re = re.compile(r"^[A-Z][A-Z0-9_]+$")
enum_value_re = re.compile(r"^[a-z0-9_]+$")
short_name_re = re.compile(r"^[A-Z][A-Za-z0-9]+$")


def update_game_py(enum_name: str, enum_value: str):
    with _GAMES_PATH.joinpath("game.py").open() as f:
        game_py = list(f)

    enum_entry = f'    {enum_name} = "{enum_value}"\n'

    try:
        game_py.index(enum_entry)
        return  # Found, abort!
    except ValueError:
        # Not found, so keep going
        pass

    enum_index = game_py.index("    def data(self) -> GameData:\n")
    game_py.insert(enum_index - 2, enum_entry)

    import_index = game_py.index('            raise ValueError(f"Missing import for game: {self.value}")\n')
    game_py.insert(import_index - 1, f"        elif self == RandovaniaGame.{enum_name}:\n")
    game_py.insert(import_index, f"            import randovania.games.{enum_value}.game_data as game_module\n")

    with _GAMES_PATH.joinpath("game.py").open("w") as f:
        f.writelines(game_py)


def copy_python_code(
    enum_name: str,
    enum_value: str,
    short_name: str,
    long_name: str,
):
    blank_root = _GAMES_PATH.joinpath(RandovaniaGame.BLANK.value)
    new_root = _GAMES_PATH.joinpath(enum_value)

    new_root.mkdir(exist_ok=True)

    # Copy cover art
    new_root.joinpath("assets").mkdir(exist_ok=True)
    shutil.copyfile(blank_root.joinpath("assets/cover.png"), new_root.joinpath("assets/cover.png"))

    # Copy game dir
    for file in blank_root.rglob("*"):
        relative = file.relative_to(blank_root)
        if relative.as_posix().startswith("assets"):
            continue

        new_path = new_root.joinpath(relative)

        if file.is_dir():
            new_path.mkdir(exist_ok=True)
            continue

        elif file.suffix != ".py":
            continue

        code = file.read_text()
        code = code.replace("randovania.games.blank", f"randovania.games.{enum_value}")
        code = class_name_re.sub(short_name + r"\1", code)
        code = code.replace("RandovaniaGame.BLANK", f"RandovaniaGame.{enum_name}")

        if relative.as_posix() == "game_data.py":
            code = code.replace('short_name="Blank"', f'short_name="{short_name}"')
            code = code.replace('long_name="Blank Development Game"', f'long_name="{long_name}"')
            code = code.replace("defaults_available_in_game_sessions=randovania.is_dev_version(),", "")

        new_root.joinpath(relative).write_text(code)


def create_new_database(game_enum: RandovaniaGame, output_path: Path) -> GameDescription:
    items = [
        ItemResourceInfo(0, "Powerful Weapon", "Weapon", 1),
        ItemResourceInfo(1, "Victory Key", "VictoryKey", 1),
        ItemResourceInfo(2, "Health", "Health", 500),
    ]

    resource_database = ResourceDatabase(
        game_enum=game_enum,
        item=items,
        event=[],
        trick=[],
        damage=[],
        version=[],
        misc=[],
        requirement_template={},
        damage_reductions={},
        energy_tank_item=items[-1],
        base_damage_reduction=default_base_damage_reduction,
    )

    dock_types = [
        DockType("Door", "Door", frozendict()),
        DockType("Other", "Other", frozendict()),
    ]
    impossible_weak = DockWeakness(0, "Not Determined", frozendict(), Requirement.impossible(), None)

    dock_weakness_database = DockWeaknessDatabase(
        dock_types,
        weaknesses={
            dock_types[0]: {"Normal": DockWeakness(0, "Normal", frozendict(), Requirement.trivial(), None)},
            dock_types[1]: {
                "Not Determined": impossible_weak,
            },
        },
        dock_rando_params={},
        default_weakness=(dock_types[1], impossible_weak),
        dock_rando_config=DockRandoConfig(
            force_change_two_way=False,
            resolver_attempts=100,
            to_shuffle_proportion=1.0,
        ),
    )

    intro_node = GenericNode(
        identifier=NodeIdentifier.create("Main", "First Area", "Spawn Point"),
        node_index=0,
        heal=False,
        location=None,
        description="",
        layers=("default",),
        extra={},
        valid_starting_location=True,
    )

    game_db = GameDescription(
        game=game_enum,
        dock_weakness_database=dock_weakness_database,
        resource_database=resource_database,
        layers=("default",),
        victory_condition=ResourceRequirement.simple(items[1]),
        starting_location=intro_node.identifier,
        initial_states={},
        minimal_logic=None,
        region_list=RegionList(
            [
                Region(
                    name="Main",
                    areas=[
                        Area(
                            name="First Area",
                            nodes=[intro_node],
                            connections={intro_node: {}},
                            extra={},
                        )
                    ],
                    extra={},
                )
            ]
        ),
    )

    data = data_writer.write_game_description(game_db)
    data_writer.write_as_split_files(data, output_path)
    pretty_print.write_human_readable_game(game_db, output_path)
    return game_db


def create_pickup_database(game_enum: RandovaniaGame):
    pickup_categories = {
        "weapon": PickupCategory(
            name="weapon",
            long_name="Weapon",
            hint_details=("a ", "weapon"),
            hinted_as_major=True,
        ),
        "ammo-based": PickupCategory(
            name="ammo-based",
            long_name="Ammo-Based",
            hint_details=("an ", "ammo-based item"),
            hinted_as_major=False,
        ),
    }
    pickup_db = PickupDatabase(
        pickup_categories=pickup_categories,
        standard_pickups={
            "Powerful Weapon": StandardPickupDefinition(
                game=game_enum,
                name="Powerful Weapon",
                pickup_category=pickup_categories["weapon"],
                broad_category=pickup_categories["ammo-based"],
                model_name="Powerful",
                offworld_models=frozendict(),
                progression=("Weapon",),
                preferred_location_category=LocationCategory.MAJOR,
            ),
        },
        ammo_pickups={},
        default_pickups={},
        default_offworld_model="Powerful",
    )
    default_database.write_pickup_database_for_game(pickup_db, game_enum)
    return pickup_db


def load_presets(template: RandovaniaGame):
    def get(path: str):
        v = VersionedPreset.from_file_sync(_GAMES_PATH.joinpath(template.value, "presets", path))
        v.get_preset()
        return v

    return {preset_config["path"]: get(preset_config["path"]) for preset_config in template.data.presets}


def copy_presets(old_presets: dict[str, VersionedPreset], gd: GameDescription, pickup_db: PickupDatabase):
    new_game = gd.game
    for path, preset in old_presets.items():
        config = preset.get_preset().configuration
        new_preset = dataclasses.replace(
            preset.get_preset(),
            uuid=uuid.uuid4(),
            game=new_game,
            configuration=dataclasses.replace(
                config,
                starting_location=StartingLocationList(
                    (gd.starting_location,),
                    new_game,
                ),
                standard_pickup_configuration=StandardPickupConfiguration(
                    game=new_game,
                    pickups_state={
                        pickup: StandardPickupState(num_shuffled_pickups=1)
                        for pickup in pickup_db.standard_pickups.values()
                    },
                    default_pickups={},
                    minimum_random_starting_pickups=0,
                    maximum_random_starting_pickups=0,
                ),
                ammo_pickup_configuration=AmmoPickupConfiguration(
                    pickups_state={},
                ),
                dock_rando=DockRandoConfiguration(
                    game=new_game,
                    mode=DockRandoMode.VANILLA,
                    types_state={
                        dock_type: DockTypeState(new_game, dock_type.short_name, set(), set())
                        for dock_type in gd.dock_weakness_database.dock_types
                    },
                ),
            ),
        )

        VersionedPreset.with_preset(new_preset).save_to_file(_GAMES_PATH.joinpath(new_game.value, "presets", path))


def new_game_command_logic(args):
    enum_name: str = args.enum_name
    enum_value: str = args.enum_value
    short_name: str = args.short_name
    long_name: str = args.long_name

    try:
        if enum_name_re.match(enum_name) is None:
            raise ValueError(f"Enum name must match {enum_name_re.pattern}")

        if enum_value_re.match(enum_value) is None:
            raise ValueError(f"Enum value must match {enum_value_re.pattern}")

        if short_name_re.match(short_name) is None:
            raise ValueError(f"Short name must match {short_name_re.pattern}")

        if '"' in long_name:
            raise ValueError("Quotes not allowed in long name")

    except ValueError as v:
        print(f"Error! {v}")
        raise SystemExit(1)

    copy_python_code(enum_name, enum_value, short_name, long_name)
    update_game_py(enum_name, enum_value)

    json_lib.write_path(_GAMES_PATH.joinpath(enum_value).joinpath("assets", "migration_data.json"), {})

    raise SystemExit(
        subprocess.run(
            [
                sys.executable,
                "-m",
                "randovania",
                "development",
                "create-new-database",
                "--game",
                enum_value,
            ],
            check=False,
        ).returncode
    )


def create_new_database_logic(args):
    new_enum = RandovaniaGame(args.game)

    game_db = create_new_database(new_enum, _GAMES_PATH.joinpath(new_enum.value).joinpath("logic_database"))
    pickup_db = create_pickup_database(new_enum)
    copy_presets(load_presets(RandovaniaGame.BLANK), game_db, pickup_db)
    print(f"{new_enum.long_name} created successfully. New files can be found at {new_enum.data_path}")


def add_new_game_command(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "add-new-game", help="Loads the preset files and saves then again with the latest version"
    )
    parser.add_argument(
        "--enum-name",
        help="The name of the RandovaniaGame enum, used in code.",
        required=True,
    )
    parser.add_argument(
        "--enum-value",
        help="The value of the RandovaniaGame enum, used in all data formats.",
        required=True,
    )
    parser.add_argument(
        "--short-name",
        help="Used as class prefix, and for user-facing strings that can't fit the long name.",
        required=True,
    )
    parser.add_argument(
        "--long-name",
        help="The full name of your game.",
        required=True,
    )
    parser.set_defaults(func=new_game_command_logic)


def add_create_databases(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "create-new-database",
        help="Creates initial databases for a recently created game. Automatically ran after add-new-game",
    )
    parser.add_argument(
        "--game",
        type=str,
        required=True,
        choices=[game.value for game in RandovaniaGame.all_games()],
        help="Use the included database for the given game.",
    )
    parser.set_defaults(func=create_new_database_logic)
