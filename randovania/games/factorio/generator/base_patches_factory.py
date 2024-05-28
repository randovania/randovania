from __future__ import annotations

import typing
from typing import TYPE_CHECKING

from randovania.games.factorio.data_importer import data_parser
from randovania.games.factorio.generator import recipes
from randovania.games.factorio.generator.complexity import complexity_calculator
from randovania.games.factorio.layout import FactorioConfiguration
from randovania.generator.base_patches_factory import BasePatchesFactory
from randovania.lib import json_lib

if TYPE_CHECKING:
    from random import Random

    from randovania.game_description.game_description import GameDescription
    from randovania.layout.base.base_configuration import BaseConfiguration


class RecipeIngredient(typing.TypedDict):
    name: str
    amount: int


class CustomRecipe(typing.TypedDict):
    ingredients: dict[str, int]


class FactorioGameSpecific(typing.TypedDict):
    recipes: dict[str, CustomRecipe]


class FactorioBasePatchesFactory(BasePatchesFactory):
    def create_game_specific(
        self, configuration: BaseConfiguration, game: GameDescription, rng: Random
    ) -> FactorioGameSpecific:
        assert isinstance(configuration, FactorioConfiguration)

        assets_folder = configuration.game.data_path.joinpath("assets")

        recipes_raw = data_parser.load_recipes_raw()
        techs_raw = json_lib.read_path(assets_folder.joinpath("techs-raw.json"))
        item_complexity = complexity_calculator(recipes_raw, techs_raw)

        # All categories
        # ['advanced-crafting', 'boiler', 'centrifuging', 'chemistry', 'crafting',
        #  'crafting-with-fluid', 'hand', 'miner', 'oil-processing', 'pump',
        #  'pumpjack', 'rocket-building', 'smelting']

        all_items = list(item_complexity.keys())

        simple_items = [
            item_name
            for item_name, complexity in item_complexity.items()
            if complexity.categories.issubset({"miner", "smelting", "crafting", "advanced-crafting"})
        ]

        to_change = {
            "automation-science-pack": (simple_items, 1),
            "logistic-science-pack": (simple_items, 1),
            "military-science-pack": (all_items, 1),
            "chemical-science-pack": (all_items, 1),
            "production-science-pack": (all_items, 1),
            "utility-science-pack": (all_items, 1),
            "rocket-part": (all_items, 0),
        }
        custom_recipes = {}

        for target_item, (items, max_fluid) in to_change.items():
            ingredients = recipes.make_random_recipe(
                rng, items, item_complexity[target_item], item_complexity, max_fluid=max_fluid
            )
            custom_recipes[target_item] = {
                "ingredients": {
                    item_name: amount * 10 if item_complexity[item_name].is_fluid else amount
                    for item_name, amount in ingredients
                }
            }

        return {
            "recipes": custom_recipes,
        }
