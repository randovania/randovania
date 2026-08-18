from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING

from randovania.game.game_enum import RandovaniaGame

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace, _SubParsersAction
    from pathlib import Path

try:
    from PIL import Image

    has_pil = True
except ImportError:
    has_pil = False


def convert_database_images_command_logic(args: Namespace) -> int:
    if not has_pil:
        print("Pillow not installed.")
        return 1

    game = RandovaniaGame(args.game)
    root_path = game.data_path.joinpath("assets", "maps")

    size_report = {}

    def convert_task(png_path: Path, webp_path: Path) -> None:
        old_size = png_path.stat().st_size
        img = Image.open(png_path)
        if args.kind == "tile-based":
            img.save(
                webp_path,
                lossless=True,
                method=6,
            )
        else:
            img.save(
                webp_path,
                quality=25,
                method=6,
            )

        new_size = webp_path.stat().st_size
        size_report[png_path.relative_to(root_path)] = (old_size, new_size)

        if new_size > old_size:
            webp_path.unlink()
            size_report[png_path.relative_to(root_path)] = (old_size, old_size)

        else:
            if args.delete_png:
                png_path.unlink()

    with ThreadPoolExecutor() as executor:
        for region in game.game_description.region_list.regions:
            region_path = root_path.joinpath(region.name)
            for area in region.areas:
                png = region_path.joinpath(f"{area.map_name}.png")
                if not png.is_file():
                    continue

                executor.submit(convert_task, png, region_path.joinpath(f"{area.map_name}.webp"))

    total_before = sum(old for old, _ in size_report.values())
    total_after = sum(new for old, new in size_report.values())
    identical = sum(1 for old, new in size_report.items() if old == new)
    print(f"Before: {total_before}; After: {total_after}; Ratio: {total_after / total_before}; Identical: {identical}")

    return 0


def add_convert_database_images_command(sub_parsers: _SubParsersAction) -> None:
    parser: ArgumentParser = sub_parsers.add_parser(
        "convert-database-images", help="Converts the database images from PNG to WebP."
    )
    parser.add_argument(
        "--game",
        type=str,
        required=True,
        choices=[game.value for game in RandovaniaGame.all_games()],
        help="The game to convert.",
    )
    parser.add_argument(
        "--delete-png",
        action="store_true",
        default=False,
        help="Deletes the png images after converting.",
    )
    parser.add_argument(
        "kind",
        choices=["tile-based", "screenshot"],
        help="What kind of images they are? Screenshots of the full scene, or tile-based scenes.",
    )

    parser.set_defaults(func=convert_database_images_command_logic)
