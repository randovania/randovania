import argparse
import dataclasses
import enum
import typing
from argparse import Namespace
from pathlib import Path

from randovania.cli.cli_lib import EnumAction
from randovania.exporter.game_exporter import GameExportParams
from randovania.games.game import RandovaniaGame
from randovania.lib import json_lib, type_lib


def _add_parser_arguments_for(
    parser: argparse.ArgumentParser, params_type: type[GameExportParams]
) -> tuple[list[str], list[str]]:
    resolved_types = typing.get_type_hints(params_type)
    field_names = []
    skipped_fields = []
    for field in dataclasses.fields(params_type):
        type_, is_optional = type_lib.resolve_optional(resolved_types[field.name])

        arg_kwargs: dict = {}
        if type_ is Path:
            arg_kwargs["type"] = type_
            arg_kwargs["required"] = not is_optional

        elif type_ is bool:
            arg_kwargs["action"] = "store_true"
            arg_kwargs["required"] = False

        elif issubclass(type_, enum.Enum):
            arg_kwargs["type"] = type_
            arg_kwargs["required"] = not is_optional
            arg_kwargs["action"] = EnumAction

        elif is_optional:
            skipped_fields.append(field.name)
            continue

        else:
            raise TypeError("Game requires arguments of an unsupported type for exporting.")

        field_names.append(field.name)
        arg_name = field.name.replace("_", "-")
        parser.add_argument(f"--{arg_name}", **arg_kwargs)

    return field_names, skipped_fields


def get_export_params_from_cli(game: RandovaniaGame, args: list[str]) -> GameExportParams:
    parser = argparse.ArgumentParser(prog=f"randovania layout export-game {game.value}")
    params_type = game.exporter.export_params_type()

    field_names, skipped_fields = _add_parser_arguments_for(parser, params_type)

    new_args = parser.parse_args(args)
    arguments = {name: getattr(new_args, name) for name in field_names}
    for skipped in skipped_fields:
        arguments[skipped] = None

    return params_type(**arguments)


def export_game_logic(args: Namespace) -> None:
    game = RandovaniaGame(args.game)

    def print_status_report(message: str, percent: float) -> None:
        print(f"[{100 * percent:3.0f}%] {message}")

    export_params = get_export_params_from_cli(game, args.args)
    patcher_data = json_lib.read_dict(args.patcher_data)

    game.exporter.export_game(patcher_data, export_params, print_status_report)


def add_export_game_command(sub_parsers: typing.Any) -> None:
    parser: argparse.ArgumentParser = sub_parsers.add_parser("export-game", help="Export a game")
    parser.add_argument("--patcher-data", required=True, type=Path, help="Path to a JSON file with the patcher data.")
    parser.add_argument("game", choices=[game.value for game in RandovaniaGame])
    parser.add_argument("args", nargs=argparse.REMAINDER)
    parser.set_defaults(func=export_game_logic)
