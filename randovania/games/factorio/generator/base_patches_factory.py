from __future__ import annotations

import typing
from typing import TYPE_CHECKING

from randovania.game_description.resources.resource_collection import ResourceCollection
from randovania.games.factorio.data_importer import data_parser
from randovania.games.factorio.generator import recipes
from randovania.games.factorio.generator.item_cost import BASIC_RESOURCES, cost_calculator
from randovania.games.factorio.layout import FactorioConfiguration
from randovania.generator.base_patches_factory import BasePatchesFactory
from randovania.generator.pickup_pool import pool_creator

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

        recipes_raw = data_parser.load_recipes_raw()
        techs_raw = data_parser.load_techs_raw()
        item_cost = cost_calculator(recipes_raw, techs_raw)

        # Get all tech that are present in the preset
        collection = ResourceCollection.with_database(game.resource_database)
        for pickup in pool_creator.calculate_pool_results(configuration, game).all_pickups():
            collection.add_resource_gain(pickup.resource_gain(collection))

        # Get all recipes available
        available_recipes = {recipe for recipe, data in recipes_raw.items() if data.get("enabled", True)}
        for tech, _ in collection.as_resource_gain():
            available_recipes.update(tech.extra["recipes_unlocked"])

        # Get all recipe results
        all_items_set = set(BASIC_RESOURCES)
        for recipe in available_recipes:
            all_items_set.update(data_parser.get_results(recipes_raw[recipe]).keys())

        all_items = sorted(all_items_set)
        simple_items = [
            item_name
            for item_name in all_items
            if item_cost[item_name].categories.issubset({"miner", "smelting", "crafting", "advanced-crafting"})
        ]

        to_change = {
            "automation-science-pack": (simple_items, 0),
            "logistic-science-pack": (simple_items, 0),
            "military-science-pack": (all_items, 1),
            "chemical-science-pack": (all_items, 2),
            "production-science-pack": (all_items, 2),
            "utility-science-pack": (all_items, 2),
            "rocket-part": (all_items, 0),
        }
        custom_recipes = {}

        for target_item, (items, max_fluid) in to_change.items():
            ingredients = recipes.make_random_recipe(rng, items, target_item, item_cost, max_fluid=max_fluid)
            custom_recipes[target_item] = {
                "ingredients": {
                    item_name: amount * 10 if item_cost[item_name].is_fluid else amount
                    for item_name, amount in ingredients
                }
            }

        return {
            "recipes": custom_recipes,
        }
