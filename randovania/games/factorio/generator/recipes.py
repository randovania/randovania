import collections
import itertools
import math
import random

from randovania.games.factorio.generator.item_cost import ItemCost, cost_for_ingredient_list, item_is_fluid
from randovania.lib import pyeasyga

_TARGET_FITNESS = 0.25


class RecipeAlgorithm(pyeasyga.GeneticAlgorithm):
    all_good_solutions: set[tuple[int, ...]]

    def __init__(
        self,
        item_names: list[str],
        seed_data: list[ItemCost],
        rng: random.Random,
        target_cost: ItemCost,
        max_fluid: int,
        max_items: int,
    ):
        population_size = 200
        generations = 10
        crossover_probability = 0.1
        mutation_probability = 0.8

        self.item_names = item_names
        self.target_cost = target_cost
        self.max_fluid = max_fluid
        self.max_items = max_items
        self.all_good_solutions = set()

        super().__init__(
            seed_data,
            population_size,
            generations,
            crossover_probability,
            mutation_probability,
            elitism=False,
            maximise_fitness=False,
            rng=rng,
        )

    def create_individual(self, seed_data: list[ItemCost]) -> pyeasyga.Genes:
        genes = [0] * len(seed_data)
        genes[self.random.randint(0, len(seed_data) - 1)] = 1
        return genes

    def create_individual_from_indices(self, indices: tuple[int, ...]) -> pyeasyga.Genes:
        genes = [0] * len(self.seed_data)
        for idx in indices:
            genes[idx] = 1
        return genes

    def mutate_function(self, individual: list[int]) -> None:
        if self.random.randrange(4) == 0:
            # 25% chance of increasing the ingredient cost of an existing ingredient
            idx = [i for i, v in enumerate(individual) if v > 0]
            if idx:
                individual[self.random.choice(idx)] += 1
                return

        mutate_index = self.random.randrange(len(individual))
        individual[mutate_index] = (0, 1)[individual[mutate_index] == 0]

    def fitness_function(self, individual: list[int], data: list[ItemCost]) -> float:
        item_count = 0
        fluid_count = 0

        ingredients = []

        for selected, item in zip(individual, data):
            if selected:
                item: ItemCost
                item_count += 1

                if item.is_fluid:
                    fluid_count += 1
                    if fluid_count > self.max_fluid:
                        return math.inf

                if item_count > self.max_items:
                    return math.inf

                ingredients.append((item, selected))

        material, complexity = cost_for_ingredient_list(ingredients)

        material_distance = math.fabs(self.target_cost.material - material) / self.target_cost.material
        complexity_distance = math.fabs(self.target_cost.complexity - complexity) / self.target_cost.complexity

        return material_distance + complexity_distance

    def create_initial_population(self) -> None:
        """Create a population with all combinations of items, of increasing size."""
        initial_population = []
        for k in itertools.count(1):
            new_genes = [
                self.create_individual_from_indices(comb)
                for comb in itertools.combinations(range(len(self.seed_data)), k)
            ]
            missing_genes = self.population_size - len(initial_population)
            if len(new_genes) - missing_genes > 0:
                self.random.shuffle(new_genes)

            initial_population.extend(pyeasyga.Chromosome(genes) for genes in new_genes[:missing_genes])
            if len(initial_population) >= self.population_size:
                break

        self.all_good_solutions = set()
        self.current_generation = initial_population

    def create_next_generation(self) -> None:
        super().create_next_generation()

        for recipe in self.current_generation:
            if recipe.fitness > _TARGET_FITNESS:
                break
            self.all_good_solutions.add(tuple(recipe.genes))


def make_random_recipe(
    rng: random.Random,
    item_pool: list[str],
    target_item: str,
    item_costs: dict[str, ItemCost],
    max_items: int = 6,
    max_fluid: int = 1,
) -> tuple[tuple[str, int], ...]:
    target_cost = item_costs[target_item]
    possible_items = [
        item_name
        for item_name in item_pool
        if item_costs[item_name].material <= target_cost.material
        and item_costs[item_name].complexity <= target_cost.complexity
        and item_name != target_item
    ]

    ga = RecipeAlgorithm(
        item_names=possible_items,
        seed_data=[item_costs[item_name] for item_name in possible_items],
        rng=rng,
        target_cost=target_cost,
        max_fluid=max_fluid,
        max_items=max_items,
    )

    def ingredient_from_genes(genes: list[int]) -> tuple[tuple[str, int], ...]:
        return tuple((possible_items[i], selected) for i, selected in enumerate(genes) if selected)

    def group_by_items(all_genes: list[tuple[int, ...]]) -> dict[tuple[int, ...], list[list[int]]]:
        groups = collections.defaultdict(list)
        for gene in all_genes:
            indices = tuple(idx for idx, selected in enumerate(gene) if selected)
            groups[indices].append(gene)

        return groups

    ga.run()

    grouped_solutions = group_by_items(sorted(ga.all_good_solutions))

    result_key = rng.choice(list(grouped_solutions.keys()))
    best_solution = min(grouped_solutions[result_key], key=lambda it: ga.fitness_function(it, ga.seed_data))
    result = ingredient_from_genes(best_solution)

    return result


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
