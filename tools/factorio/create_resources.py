import argparse
import csv
import json
import typing
from pathlib import Path

from randovania.games.factorio.data_importer import data_parser
from randovania.lib import json_lib
from tools.factorio import util
from tools.factorio.util import and_req, or_req, tech_req, template_req

_k_items_for_crafting_category = {
    "crafting": [],
    "advanced-crafting": ["assembling-machine-1"],  # , "assembling-machine-2", "assembling-machine-3"],
    "smelting": [],  # ["stone-furnace", "steel-furnace", "electric-furnace"],
    "chemistry": ["chemical-plant"],
    "crafting-with-fluid": ["assembling-machine-2"],  # , "assembling-machine-3"],
    "oil-processing": ["oil-refinery"],
    "rocket-building": ["rocket-silo"],
    "centrifuging": ["centrifuge"],
}

_k_burner_entities = [
    "stone-furnace",
    "steel-furnace",
    "boiler",
    "burner-mining-drill",
]
_k_electric_entities = [
    "assembling-machine-1",
    "assembling-machine-2",
    "assembling-machine-3",
    "electric-furnace",
    "chemical-plant",
    "oil-refinery",
    "rocket-silo",
    "centrifuge",
    "electric-mining-drill",
    "pumpjack",
]

_k_fuel_production = template_req("craft-coal")

# _k_basic_mining = or_req(
#     [
#         template_req("use-burner-mining-drill"),
#         template_req("use-electric-mining-drill"),
#     ]
# )
_k_basic_mining = and_req([])

_k_miner_for_resource = {
    "raw-fish": and_req([]),
    "wood": and_req([]),
    "coal": and_req([]),  # coal is needed for power, so let's keep it simple to avoid loops
    # Rn, can always mine
    "iron-ore": _k_basic_mining,
    "copper-ore": _k_basic_mining,
    "stone": _k_basic_mining,
    "water": template_req("has-offshore-pump"),
    "steam": or_req(
        [
            and_req(
                [
                    template_req("has-boiler"),
                    _k_fuel_production,
                ],
                comment="Boiler powered Steam Engines",
            ),
            # Causes loops with coal liquefaction
            # and_req(
            #     [
            #         item_req("nuclear-reactor"),
            #         template_req("craft-uranium-fuel-cell"),
            #     ],
            #     comment="Nuclear Power",
            # ),
        ]
    ),
    "uranium-ore": and_req(
        [
            template_req("use-electric-mining-drill"),
            template_req("craft-sulfuric-acid"),
            tech_req("uranium-mining"),
        ]
    ),
    "crude-oil": template_req("use-pumpjack"),
}


def requirement_for_recipe(recipes_raw: dict, recipe: str, unlocking_techs: list[str]) -> dict:
    entries = []

    if len(unlocking_techs) > 1:
        entries.append(or_req([tech_req(tech) for tech in unlocking_techs]))
    elif unlocking_techs:
        entries.append(tech_req(unlocking_techs[0]))

    category = recipes_raw[recipe].get("category", "crafting")

    if category != "crafting":  # hand-craft compatible, so assume always possible
        entries.append(template_req(f"perform-{category}"))

    for ingredient in recipes_raw[recipe]["ingredients"]:
        if isinstance(ingredient, dict):
            ing_name = ingredient["name"]
        else:
            ing_name = ingredient[0]

        if recipe == "kovarex-enrichment-process" and ing_name == "uranium-235":
            continue

        entries.append(template_req(f"craft-{ing_name}"))

    return and_req(entries)


def create_resources(header: dict, techs_for_recipe: dict) -> None:
    header["resource_database"]["items"] = {}

    for tech_name, recipes_unlocked in techs_for_recipe.items():
        header["resource_database"]["items"][tech_name] = {
            "long_name": util.get_localized_name(tech_name),
            "max_capacity": 1,
            "extra": {"recipes_unlocked": recipes_unlocked},
        }


def update_templates(header: dict, recipes_raw: dict, techs_for_recipe: dict[str, list[str]]):
    header["resource_database"]["requirement_template"]["has-electricity"] = {
        "display_name": "Has Electricity",
        "requirement": or_req(
            [
                and_req(
                    [
                        tech_req("steam-power"),
                        _k_fuel_production,
                    ],
                    comment="Boiler powered Steam Engines",
                ),
                and_req(
                    [tech_req("solar-energy"), tech_req("electric-energy-accumulators")],
                    comment="Solar with battery for night",
                ),  # TODO: maybe craft?
                # TODO: figure out settings later
                # and_req([item_req("solar-energy"), setting("solar-without-accumulator")]),
                # Nuclear requires electricity to work
                # and_req(
                #     [
                #         item_req("nuclear-power"),
                #         template_req("craft-uranium-fuel-cell"),
                #     ],
                #     comment="Nuclear Power",
                # ),
            ]
        ),
    }

    for entity in _k_burner_entities:
        header["resource_database"]["requirement_template"][f"use-{entity}"] = {
            "display_name": f"Use {entity}",
            "requirement": and_req(
                [template_req(f"has-{entity}"), _k_fuel_production],
                comment="Fuel is considered always available.",
            ),
        }

    for entity in _k_electric_entities:
        header["resource_database"]["requirement_template"][f"use-{entity}"] = {
            "display_name": f"Use {entity}",
            "requirement": and_req(
                [
                    template_req(f"has-{entity}"),
                    template_req("has-electricity"),
                ]
            ),
        }

    # Machines needed for the non-trivial crafting recipes
    for category, items in _k_items_for_crafting_category.items():
        header["resource_database"]["requirement_template"][f"perform-{category}"] = {
            "display_name": f"Perform {category}",
            "requirement": or_req([template_req(f"use-{it}") for it in items]) if items else and_req([]),
        }

    # Add the templates for crafting all recipes
    for item_name, recipes in data_parser.get_recipes_for(recipes_raw).items():
        localized_name = util.get_localized_name(item_name)

        techs = set()
        for recipe in recipes:
            techs.update(techs_for_recipe.get(recipe, []))

        header["resource_database"]["requirement_template"][f"has-{item_name}"] = {
            "display_name": f"Unlocked {localized_name}",
            "requirement": or_req([tech_req(tech) for tech in sorted(techs)]) if techs else and_req([]),
        }
        header["resource_database"]["requirement_template"][f"craft-{item_name}"] = {
            "display_name": f"Craft {localized_name}",
            "requirement": or_req(
                [
                    requirement_for_recipe(recipes_raw, recipe, techs_for_recipe.get(recipe, []))
                    for recipe in sorted(recipes)
                ]
            ),
        }

    # Mining all resources
    for resource_name, requirement in _k_miner_for_resource.items():
        localized_name = util.get_localized_name(resource_name)
        header["resource_database"]["requirement_template"][f"craft-{resource_name}"] = {
            "display_name": f"Mine {localized_name}",
            "requirement": requirement,
        }


def read_tech_csv(csv_path: Path) -> dict:
    result = {}

    with csv_path.open() as f:
        f.readline()
        r = csv.reader(f)
        for line in r:
            if line[1] == "<>":
                continue

            tech_name, pickup_name, progressive_tier, category = line[:4]
            # print(tech_name, pickup_name, progressive_tier, category)
            result[tech_name] = {
                "pickup_name": pickup_name,
                "progressive_tier": progressive_tier,
                "category": category,
            }

    return result


_custom_shuffled_count = {
    "Laser Weapons Damage": 0,
    "Follower Robot Count": 0,
    "Laser Shooting Speed": 0,
    "Mining Productivity": 4,
    "Physical Projectile Damage": 0,
    "Refined Flammables": 0,
    "Regular Inserter Capacity Bonus": 3,
    "Research Speed": 5,
    "Bulk Inserter Capacity Bonus": 4,
    "Stronger Explosives": 0,
    "Research Productivity": 5,
    "Toolbelt": 3,
    "Weapon Shooting Speed": 0,
    "Worker Robots Speed": 5,
    "Worker Robots Storage": 5,
}


def create_pickups(techs_raw: dict, existing_pickup_ids: dict[str, int], tech_csv: dict) -> dict:
    result = {}

    for tech_name, data in tech_csv.items():
        pickup_name = data["pickup_name"]
        if pickup_name in result:
            result[pickup_name]["progression"].append(tech_name)
            if tech_name in existing_pickup_ids:
                if "original_locations" in result[pickup_name]:
                    result[pickup_name]["original_locations"].append(existing_pickup_ids[tech_name])
        else:
            tech = techs_raw[tech_name]
            if "icons" in tech:
                icon = tech["icons"][0]["icon"]
            else:
                icon = tech["icon"]

            result[pickup_name] = {
                "pickup_category": data["category"],
                "broad_category": data["category"],
                "model_name": icon,
                "offworld_models": {},
                "progression": [tech_name],
                "preferred_location_category": "major" if data["category"] != "enhancement" else "minor",
                "expected_case_for_describer": "shuffled",
            }
            if tech_name in existing_pickup_ids:
                result[pickup_name]["original_locations"] = [existing_pickup_ids[tech_name]]

            if pickup_name in _custom_shuffled_count:
                if _custom_shuffled_count[pickup_name] == 0:
                    result[pickup_name]["expected_case_for_describer"] = "missing"
                else:
                    result[pickup_name]["custom_count_for_shuffled_case"] = _custom_shuffled_count[pickup_name]

    for pickup in result.values():
        if len(pickup["progression"]) > 1:
            pickup["description"] = "Provides in order: " + " → ".join(
                util.get_localized_name(tech_name) for tech_name in pickup["progression"]
            )

    result["Uranium Mining"]["expected_case_for_describer"] = "starting_item"
    result["Rocket Silo"]["expected_case_for_describer"] = "vanilla"
    result["Rocket Silo"]["hide_from_gui"] = True

    return result


def remove_unwanted_tech(tech_raw: dict[str, dict], tech_csv) -> dict:
    def filter_tech(name: str) -> bool:
        if name not in tech_csv:
            return False

        return not name.startswith("randovania-")

    return {key: value for key, value in tech_raw.items() if filter_tech(key)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--factorio", type=Path, help="Path to the Factorio root folder.", required=True)
    parser.add_argument("--tech-csv", type=Path, help="Path to the CSV with tech definitions.", required=True)
    args = parser.parse_args()

    factorio_path: Path = args.factorio
    csv_path: Path = args.tech_csv

    rdv_factorio_path = Path(__file__).parents[2].joinpath("randovania/games/factorio")
    pickup_db_path = rdv_factorio_path.joinpath("pickup_database/pickup-database.json")
    header_path = rdv_factorio_path.joinpath("logic_database/header.json")

    raw_dump_path = factorio_path.joinpath("script-output/data-raw-dump.json")
    util.read_locales(factorio_path)
    tech_csv = read_tech_csv(csv_path)

    existing_pickup_ids = util.load_existing_pickup_ids(rdv_factorio_path.joinpath("logic_database/Tech.json"))

    with raw_dump_path.open() as f:
        raw_dump: dict[str, dict[str, typing.Any]] = json.load(f)

    recipes_raw = raw_dump["recipe"]
    data_parser.remove_expensive(recipes_raw)

    techs_raw = remove_unwanted_tech(raw_dump["technology"], tech_csv)

    json_lib.write_path(rdv_factorio_path.joinpath("assets", "recipes-raw.json"), recipes_raw)
    json_lib.write_path(rdv_factorio_path.joinpath("assets", "techs-raw.json"), techs_raw)

    with header_path.open() as f:
        header = json.load(f)

    header["resource_database"]["requirement_template"] = {}

    with pickup_db_path.open() as f:
        pickup_db = json.load(f)

    create_resources(header, data_parser.get_recipes_unlock_by_tech(techs_raw))
    update_templates(header, recipes_raw, data_parser.get_techs_for_recipe(techs_raw))

    pickup_db["standard_pickups"] = create_pickups(techs_raw, existing_pickup_ids, tech_csv)

    header["resource_database"]["requirement_template"] = dict(
        sorted(header["resource_database"]["requirement_template"].items(), key=lambda it: it[1]["display_name"])
    )

    with header_path.open("w") as f:
        json.dump(header, f, indent=4)

    with pickup_db_path.open("w") as f:
        json.dump(pickup_db, f, indent=4)


if __name__ == "__main__":
    main()
