import math
import random
import time

from randovania.games.factorio.generator.complexity import Complexity, fitness_for, item_is_fluid
from randovania.lib import pyeasyga


def make_random_recipe(
    rng: random.Random,
    item_pool: list[str],
    target_complexity: Complexity,
    item_complexity: dict[str, Complexity],
    max_items: int = 6,
    max_fluid: int = 1,
) -> tuple[tuple[str, int], ...]:
    target_fitness = fitness_for(target_complexity.cost, target_complexity.craft)
    good_enough_fitness = target_fitness * 0.9

    possible_items = [
        item_name
        for item_name in item_pool
        if item_complexity[item_name].cost < target_complexity.cost
        and item_complexity[item_name].craft < target_complexity.craft
    ]

    ga = pyeasyga.GeneticAlgorithm(
        seed_data=[item_complexity[item_name] for item_name in possible_items],
        population_size=200,
        crossover_probability=0.2,
        mutation_probability=0.8,
        rng=rng,
    )

    def create_individual(seed_data):
        genes = [0] * len(seed_data)
        genes[rng.randint(0, len(seed_data) - 1)] = 1
        return genes

    def mutate_function(individual: list[int]) -> None:
        if rng.randrange(4) == 0:
            # 25% chance of increasing the ingredient cost of an existing ingredient
            idx = [i for i, v in enumerate(individual) if v > 0]
            if idx:
                individual[rng.choice(idx)] += 1
                return

        mutate_index = rng.randrange(len(individual))
        individual[mutate_index] = (0, 1)[individual[mutate_index] == 0]

    ga.create_individual = create_individual
    ga.mutate_function = mutate_function

    def fitness(individual: list[int], data: list[Complexity]) -> float:
        cost, craft = 0.0, 1
        item_count = 0
        fluid_count = 0

        for selected, item in zip(individual, data):
            if selected:
                item: Complexity
                item_count += 1

                extra_cost, extra_craft = item.ingredient_cost(selected)
                cost += extra_cost
                craft += extra_craft

                if item.is_fluid:
                    fluid_count += 1
                    if fluid_count > max_fluid:
                        return 0

                if item_count > max_items:
                    return 0

        if cost > target_complexity.cost or craft > target_complexity.craft:
            return 0

        target = fitness_for(cost, craft)
        return min(target_fitness - math.fabs(target - target_fitness), good_enough_fitness)

    ga.fitness_function = fitness

    def ingredient_from_genes(genes: list[int]) -> tuple[tuple[str, int], ...]:
        return tuple((possible_items[i], selected) for i, selected in enumerate(genes) if selected)

    time.time()
    ga.run()
    time.time()

    valid_solutions = {
        (gens.fitness, ingredient_from_genes(gens.genes))
        for gens in ga.current_generation
        if gens.fitness >= good_enough_fitness
    }
    result = rng.choice(sorted(valid_solutions))

    # print("REFERENCE", target_fitness, "ACTUAL", result[0])
    # print(reference_item, result[1])
    return result[1]


def determine_recipe_category(recipe_name: str, base_category: str, ingredients: dict[str, int]) -> str:
    """Adjust the building necessary for a recipe as needed, based on number of fluid inputs."""
    category = base_category
    num_fluids = sum(1 for item in ingredients if item_is_fluid(item))

    match num_fluids:
        case 0:
            pass
        case 1:
            if base_category not in {"chemistry", "oil-processing"}:
                category = "crafting-with-fluid"
        case 2:
            if base_category != "oil-processing":
                category = "chemistry"
        case 3:
            category = "oil-processing"
        case _:
            raise ValueError("Unable to create recipe with more than 3 fluids")

    if recipe_name == "rocket-part":
        category = "rocket-building"
        if num_fluids > 0:
            raise ValueError("Rocket Silo must have no fluid inputs")

    return category
