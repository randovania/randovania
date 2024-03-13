from __future__ import annotations

import argparse
import shutil
from argparse import ArgumentParser
from pathlib import Path

import yaml

from randovania import get_readme_section
from randovania.games.game import RandovaniaGame


def export_videos_yaml_command_logic(args):
    from randovania.cli.commands.export_db_videos import export_as_yaml

    games = []

    if args.game is not None:
        games.append(RandovaniaGame(args.game))
    else:
        games = list(RandovaniaGame)

    for game in games:
        export_as_yaml(game, args.output_dir, args.as_frontmatter)


def create_export_videos_yaml_command(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "export-videos-yaml",
        help="Export the video database in YAML format.",
        formatter_class=argparse.MetavarTypeHelpFormatter,
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default="exported_videos",
        help="Folder to write yaml file to.",
    )
    parser.add_argument(
        "--game",
        type=str,
        default=None,
        help="Game to export videos for.",
    )
    parser.add_argument(
        "--as-frontmatter",
        action="store_true",
        default=False,
        help="Saves the file as a .md file with frontmatter for use with Jekyll.",
    )
    parser.set_defaults(func=export_videos_yaml_command_logic)


def export_readme_sections(section: str, out_dir: Path):
    md = get_readme_section(section)
    out_dir.joinpath(f"{section.lower()}.md").write_text(md)


def export_readme_sections_logic(args):
    export_readme_sections(args.section, args.output_dir)


def create_readme_sections_command(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "export-readme-section",
        help="Extract a specific section of the readme.",
        formatter_class=argparse.MetavarTypeHelpFormatter,
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default="readme",
        help="Folder to write md file to.",
    )
    parser.add_argument(
        "--section",
        type=str,
        required=True,
        help="Which section to export.",
    )
    parser.set_defaults(func=export_readme_sections_logic)


def extract_game_data(game: RandovaniaGame, games_dir: Path, covers_dir: Path):
    # copy cover art
    shutil.copyfile(
        game.data_path.joinpath("assets/cover.png"),
        covers_dir.joinpath(f"{game.value}.png"),
    )

    data = game.data

    output = {
        "game-id": game.value,
        "short-name": game.short_name,
        "long-name": game.long_name,
        "randomize": list(data.web_info.what_can_randomize),
        "need-to-play": list(data.web_info.need_to_play),
        "multiworld": data.defaults_available_in_game_sessions,
        "development-state": data.development_state.value,
        "faq": [{"question": question, "answer": answer} for question, answer in data.faq],
    }

    yaml_body = yaml.dump(output)
    md_body = f"---\n{yaml_body}\n---"

    games_dir.joinpath(f"{game.value}.md").write_text(md_body)


def extract_game_data_logic(args):
    games = []

    if args.game is not None:
        games.append(RandovaniaGame(args.game))
    else:
        games = list(RandovaniaGame)

    for game in games:
        extract_game_data(game, args.games_dir, args.covers_dir)


def create_extract_game_data_command(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "extract-game-data",
        help="Extract the game data",
        formatter_class=argparse.MetavarTypeHelpFormatter,
    )
    parser.add_argument(
        "--games-dir",
        type=Path,
        default="_games",
        help="Folder to write games markdown file to.",
    )
    parser.add_argument(
        "--covers-dir",
        type=Path,
        default="assets/games",
        help="Folder to write games cover file to.",
    )
    parser.add_argument(
        "--game",
        type=str,
        default=None,
        help="Game to export videos for.",
    )
    parser.set_defaults(func=extract_game_data_logic)
