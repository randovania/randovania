from __future__ import annotations

import dataclasses
import math

from randovania.games.factorio.data_importer import data_parser

_k_fluids = {"water", "steam", "crude-oil", "heavy-oil", "light-oil", "petroleum-gas", "lubricant", "sulfuric-acid"}
_COMPLEXITY_PER_INGREDIENT = 2


def fitness_for(cost: float, craft: int) -> float:
    return cost + craft


@dataclasses.dataclass(order=True)
class Complexity:
    cost: float
    craft: int
    categories: set[str]
    is_fluid: bool = False

    def combine(self, cost: float, craft: int, categories: set[str]) -> Complexity:
        return Complexity(self.cost + cost, self.craft + craft, self.categories | categories)

    def ingredient_cost(self, amount: int) -> tuple[float, int]:
        return amount * self.cost, self.craft + _COMPLEXITY_PER_INGREDIENT


def complexity_calculator(recipes_raw: dict[str, dict], techs_raw: dict[str, dict]) -> dict[str, Complexity]:
    processing_items = set()
    item_complexity: dict[str, Complexity] = {}

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

    for it in list(item_complexity):
        print(f"cost for `{it}`: {item_complexity[it]}")

    def complexity_for_recipe(recipe: dict) -> Complexity:
        cost = 0
        craft = 1
        categories = {recipe.get("category", "crafting")}

        for ingredient in recipe["ingredients"]:
            if isinstance(ingredient, list):
                assert len(ingredient) == 2
                item_name, amount = ingredient
            else:
                assert isinstance(ingredient, dict)
                item_name, amount = ingredient["name"], ingredient["amount"]

            nested = complexity_for_item(item_name)
            extra_cost, extra_craft = nested.ingredient_cost(amount)
            cost += extra_cost
            craft += extra_craft
            categories |= nested.categories

        return Complexity(cost, craft, categories)

    def complexity_for_item(item_name: str) -> Complexity:
        if item_name in item_complexity:
            return item_complexity[item_name]

        if item_name in processing_items:
            raise ValueError(f"Loop when looking at {item_name}")
        processing_items.add(item_name)

        complexities = {}

        # for recipe
        for recipe_name in sorted(item_to_recipe[item_name]):
            recipe = recipes_raw[recipe_name]
            count = data_parser.count_for_result(recipe, item_name)
            recipe_complex = complexity_for_recipe(recipe)
            complexities[recipe_name] = dataclasses.replace(recipe_complex, cost=recipe_complex.cost / count)

        if complexities:
            if len(complexities) > 1:
                complexity = min(complexities.values(), key=lambda it: fitness_for(it.craft, it.cost))
            else:
                complexity = next(iter(complexities.values()))
        else:
            raise ValueError(f"No recipes for {item_name}")

        item_complexity[item_name] = dataclasses.replace(complexity, is_fluid=item_name in _k_fluids)
        processing_items.remove(item_name)
        return complexity

    item_complexity["iron-ore"] = Complexity(5.0, 1, {"miner"})
    item_complexity["copper-ore"] = Complexity(5.0, 1, {"miner"})
    item_complexity["coal"] = Complexity(5.0, 1, {"miner"})
    item_complexity["stone"] = Complexity(5.0, 1, {"miner"})
    item_complexity["water"] = Complexity(0.0, 1, {"pump"}, is_fluid=True)
    item_complexity["steam"] = Complexity(1.0, 2, {"boiler"}, is_fluid=True)
    item_complexity["crude-oil"] = Complexity(2.0, 5, {"pumpjack"}, is_fluid=True)
    item_complexity["wood"] = Complexity(math.inf, 1, {"hand"})
    item_complexity["raw-fish"] = Complexity(math.inf, 1, {"hand"})
    item_complexity["uranium-ore"] = complexity_for_item("sulfuric-acid").combine(5.0, 10, {"miner"})
    item_complexity["uranium-235"] = complexity_for_item("uranium-238").combine(1.0, 20, {"centrifuging"})

    for it in list(item_to_recipe):
        complexity_for_item(it)

    return item_complexity


def item_is_fluid(item_name: str) -> bool:
    return item_name in _k_fluids
