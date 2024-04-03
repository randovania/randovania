from __future__ import annotations

import pprint
import typing
from typing import TYPE_CHECKING

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
    type: str


class CustomRecipe(typing.TypedDict):
    recipe_name: str
    category: str
    result_amount: int
    ingredients: list[RecipeIngredient]


class FactorioGameSpecific(typing.TypedDict):
    recipes: list[CustomRecipe]


class FactorioBasePatchesFactory(BasePatchesFactory):
    def create_game_specific(
        self, configuration: BaseConfiguration, game: GameDescription, rng: Random
    ) -> FactorioGameSpecific:
        assert isinstance(configuration, FactorioConfiguration)

        assets_folder = configuration.game.data_path.joinpath("assets")

        recipes_raw = json_lib.read_path(assets_folder.joinpath("recipes-raw.json"))
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

        def recipe_ingredient(item_name: str, amount: int) -> RecipeIngredient:
            the_type = "item"
            if item_complexity[item_name].is_fluid:
                the_type = "fluid"
                amount *= 10
            return {"name": item_name, "amount": amount, "type": the_type}

        to_change = {
            "automation-science-pack": (simple_items, 1),
            "logistic-science-pack": (simple_items, 1),
            "military-science-pack": (all_items, 1),
            "chemical-science-pack": (all_items, 1),
            "production-science-pack": (all_items, 1),
            "utility-science-pack": (all_items, 1),
            "rocket-part": (all_items, 0),
        }
        custom_recipes = []

        for target_item, (items, max_fluid) in to_change.items():
            ingredients = recipes.make_random_recipe(
                rng, items, item_complexity[target_item], item_complexity, max_fluid=max_fluid
            )
            if target_item == "rocket-part":
                category = "rocket-building"
            elif any(item_complexity[item].is_fluid for item, _ in ingredients):
                category = "crafting-with-fluid"
            else:
                category = "crafting"

            custom_recipes.append(
                {
                    "recipe_name": target_item,
                    "category": category,
                    "result_amount": 1,
                    "ingredients": [recipe_ingredient(item_name, amount) for item_name, amount in ingredients],
                }
            )

        pprint.pp(custom_recipes)

        return {
            "recipes": custom_recipes,
        }
