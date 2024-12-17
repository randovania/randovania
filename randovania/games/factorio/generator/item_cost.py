from __future__ import annotations

import dataclasses
import math

from randovania.games.factorio.data_importer import data_parser

BASIC_RESOURCES = {"water", "steam", "crude-oil", "iron-ore", "copper-ore", "coal", "stone"}
_FLUID_NAMES = {"water", "steam", "crude-oil", "heavy-oil", "light-oil", "petroleum-gas", "lubricant", "sulfuric-acid"}
_COMPLEXITY_PER_INGREDIENT = 2


@dataclasses.dataclass(order=True)
class ItemCost:
    material: float
    complexity: float
    steps: int
    categories: set[str]
    is_fluid: bool = False

    def combine(self, material: float, complexity: int, categories: set[str]) -> ItemCost:
        return ItemCost(
            self.material + material, self.complexity + complexity, self.steps + 1, self.categories | categories
        )

    def ingredient_cost(self, amount: int) -> tuple[float, float]:
        return amount * self.material, self.complexity + _COMPLEXITY_PER_INGREDIENT


def cost_for_ingredient_list(ingredients: list[tuple[ItemCost, int]]) -> tuple[float, float]:
    material = 0.0
    complexity = 1.0

    for ingredient, amount in ingredients:
        material += ingredient.material * amount
        complexity += ingredient.complexity * 0.1

    complexity *= 0.5 + len(ingredients) / 2

    return material, complexity


def cost_calculator(recipes_raw: dict[str, dict], techs_raw: dict[str, dict]) -> dict[str, ItemCost]:
    processing_items = set()
    item_costs: dict[str, ItemCost] = {}

    item_to_recipe = data_parser.get_recipes_for(recipes_raw)
    techs_for_recipe = data_parser.get_techs_for_recipe(techs_raw)

    def can_ever_craft(item_name: str) -> bool:
        for recipe_name in item_to_recipe[item_name]:
            if recipe_name in techs_for_recipe:
                return True
            if recipes_raw[recipe_name].get("enabled", True):
                return True
        return False

    # Remove debug items and similar
    # Plus satellite since it's gone for now
    for it in list(item_to_recipe):
        if not can_ever_craft(it):
            del item_to_recipe[it]

    for it in list(item_costs):
        print(f"cost for `{it}`: {item_costs[it]}")

    def cost_for_recipe(recipe: dict) -> ItemCost:
        steps = 0
        categories = {recipe.get("category", "crafting")}

        ingredients = []

        for ingredient in recipe["ingredients"]:
            if isinstance(ingredient, list):
                assert len(ingredient) == 2
                item_name, amount = ingredient
            else:
                assert isinstance(ingredient, dict)
                item_name, amount = ingredient["name"], ingredient["amount"]

            nested = cost_for_item(item_name)
            ingredients.append((nested, amount))
            steps = max(steps, nested.steps)
            categories |= nested.categories

        material, complexity = cost_for_ingredient_list(ingredients)

        return ItemCost(material, complexity, steps + 1, categories)

    def cost_for_item(item_name: str) -> ItemCost:
        if item_name in item_costs:
            return item_costs[item_name]
        if item_name in processing_items:
            raise ValueError(f"Loop when looking at {item_name}")
        processing_items.add(item_name)

        costs = {}

        # for recipe
        for recipe_name in sorted(item_to_recipe[item_name]):
            recipe = recipes_raw[recipe_name]
            count = data_parser.count_for_result(recipe, item_name)
            recipe_complex = cost_for_recipe(recipe)
            costs[recipe_name] = dataclasses.replace(recipe_complex, material=recipe_complex.material / count)

        if costs:
            if len(costs) > 1:
                cost = min(costs.values(), key=lambda it: it.complexity + it.material)
            else:
                cost = next(iter(costs.values()))
        else:
            raise ValueError(f"No recipes for {item_name}")

        item_costs[item_name] = dataclasses.replace(cost, is_fluid=item_name in _FLUID_NAMES)
        processing_items.remove(item_name)
        return cost

    item_costs["iron-ore"] = ItemCost(5.0, 1, 0, {"miner"})
    item_costs["copper-ore"] = ItemCost(5.0, 1, 0, {"miner"})
    item_costs["coal"] = ItemCost(5.0, 1, 0, {"miner"})
    item_costs["stone"] = ItemCost(5.0, 1, 0, {"miner"})
    item_costs["water"] = ItemCost(0.0, 1, 0, {"pump"}, is_fluid=True)
    item_costs["steam"] = ItemCost(1.0, 2, 1, {"boiler"}, is_fluid=True)
    item_costs["crude-oil"] = ItemCost(2.0, 4, 0, {"pumpjack"}, is_fluid=True)
    item_costs["wood"] = ItemCost(math.inf, 1, 0, {"hand"})
    item_costs["raw-fish"] = ItemCost(math.inf, 1, 0, {"hand"})
    item_costs["uranium-ore"] = cost_for_item("sulfuric-acid").combine(5.0, 2, {"miner"})
    item_costs["uranium-235"] = cost_for_item("uranium-238").combine(1.0, 4, {"centrifuging"})

    for it in list(item_to_recipe):
        cost_for_item(it)

    return item_costs


def item_is_fluid(item_name: str) -> bool:
    return item_name in _FLUID_NAMES
