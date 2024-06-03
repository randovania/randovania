import argparse
import collections
import csv
import json
from pathlib import Path
from typing import TYPE_CHECKING

from randovania.layout.layout_description import LayoutDescription
from randovania.lib import json_lib

if TYPE_CHECKING:
    from randovania.games.factorio.generator.base_patches_factory import FactorioGameSpecific


def iterate_with_log(x):
    try:
        import tqdm

        return tqdm.tqdm(x)
    except ImportError:
        print("WARNING: tqdm not found. Use `pip install tqdm` to have progress feedback.")
        return x


def create_report(
    seeds_dir: Path,
    output_file: Path,
) -> None:
    seed_files = list(seeds_dir.glob(f"**/*.{LayoutDescription.file_extension()}"))

    with_amounts = collections.defaultdict(lambda: collections.defaultdict(int))
    without_amounts = collections.defaultdict(lambda: collections.defaultdict(int))
    item_frequency = collections.defaultdict(lambda: collections.defaultdict(int))
    total = 0

    for seed in iterate_with_log(seed_files):
        try:
            seed_data = json_lib.read_dict(seed)
        except json.JSONDecodeError:
            continue

        for i, game_modification in enumerate(seed_data["game_modifications"]):
            game_specific: FactorioGameSpecific = game_modification["game_specific"]
            total += 1

            for recipe_name, data in game_specific["recipes"].items():
                no_amn_ingre = ",".join(data["ingredients"].keys())
                full_thing = ",".join(f"{k}x{v}" for k, v in data["ingredients"].items())

                without_amounts[recipe_name][no_amn_ingre] += 1
                with_amounts[recipe_name][full_thing] += 1
                for k in data["ingredients"].keys():
                    item_frequency[k][recipe_name] += 1

    possible_columns = ["item name"]
    possible_columns.extend(with_amounts.keys())

    with output_file.open("w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=possible_columns)
        writer.writeheader()

        for item_name in item_frequency.keys():
            writer.writerow(
                {
                    "item name": item_name,
                    **{recipe_name: count / total for recipe_name, count in item_frequency[item_name].items()},
                }
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("seeds_dir", type=Path)
    parser.add_argument("output_file", type=Path)
    args = parser.parse_args()
    create_report(args.seeds_dir, args.output_file)


if __name__ == "__main__":
    main()
