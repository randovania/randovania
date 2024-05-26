"""
    pyeasyga module

A simple and easy-to-use genetic algorithm implementation library in Python.

For a bit array solution representation, simply instantiate the
GeneticAlgorithm class with input data, define and supply a fitness function,
run the Genetic Algorithm, and retrieve the solution!

Other solution representations will require setting some more attributes.

This library was embedded in Randovania to allow for the following modifications:
- Receive a Random object instead of using the global random
- Optimize by not deep copying unmodified elements.

__author__ = 'Ayodeji Remi-Omosowon'
__email__ = 'remiomosowon@gmail.com'
__version__ = '0.3.1'

Copyright (c) 2014, Ayodeji Remi-Omosowon
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided
that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this list of conditions and the
following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following
disclaimer in the documentation and/or other materials provided with the distribution.

* Neither the name of pyeasyga nor the names of its contributors may be used to endorse or promote products derived
from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import copy
import random
import typing
from operator import attrgetter

SeedData = typing.TypeVar("SeedData")
Fitness: typing.TypeAlias = float
Genes: typing.TypeAlias = list[int]


class GeneticAlgorithm:
    tournament_size: int
    fitness_function: typing.Callable[[Genes, list[SeedData]], Fitness] | None

    """Genetic Algorithm class.

    This is the main class that controls the functionality of the Genetic
    Algorithm.

    A simple example of usage:

    >>> # Select only two items from the list and maximise profit
    >>> from pyeasyga.pyeasyga import GeneticAlgorithm
    >>> input_data = [('pear', 50), ('apple', 35), ('banana', 40)]
    >>> easyga = GeneticAlgorithm(input_data)
    >>> def fitness (member, data):
    >>>     return sum([profit for (selected, (fruit, profit)) in
    >>>                 zip(member, data) if selected and
    >>>                 member.count(1) == 2])
    >>> easyga.fitness_function = fitness
    >>> easyga.run()
    >>> print easyga.best_individual()

    """

    def __init__(
        self,
        seed_data: list[SeedData],
        population_size: int = 50,
        generations: int = 100,
        crossover_probability: float = 0.8,
        mutation_probability: float = 0.2,
        elitism: bool = True,
        maximise_fitness: bool = True,
        rng: random.Random | None = None,
    ):
        """Instantiate the Genetic Algorithm.

        :param seed_data: input data to the Genetic Algorithm
        :type seed_data: list of objects
        :param int population_size: size of population
        :param int generations: number of generations to evolve
        :param float crossover_probability: probability of crossover operation
        :param float mutation_probability: probability of mutation operation

        """

        if rng is None:
            rng = random.Random()

        self.seed_data = seed_data
        self.population_size = population_size
        self.generations = generations
        self.crossover_probability = crossover_probability
        self.mutation_probability = mutation_probability
        self.elitism = elitism
        self.maximise_fitness = maximise_fitness
        self.random = rng

        self.current_generation: list[Chromosome] = []

        def create_individual(seed_data: list[SeedData]) -> Genes:
            """Create a candidate solution representation.

            e.g. for a bit array representation:

            >>> return [random.randint(0, 1) for _ in range(len(data))]

            :param seed_data: input data to the Genetic Algorithm
            :type seed_data: list of objects
            :returns: candidate solution representation as a list

            """
            return [rng.randint(0, 1) for _ in range(len(seed_data))]

        def crossover(parent_1: Genes, parent_2: Genes) -> tuple[Genes, Genes]:
            """Crossover (mate) two parents to produce two children.

            :param parent_1: candidate solution representation (list)
            :param parent_2: candidate solution representation (list)
            :returns: tuple containing two children

            """
            index = rng.randrange(1, len(parent_1))
            child_1 = parent_1[:index] + parent_2[index:]
            child_2 = parent_2[:index] + parent_1[index:]
            return child_1, child_2

        def mutate(individual: Genes) -> None:
            """Reverse the bit of a random index in an individual."""
            mutate_index = rng.randrange(len(individual))
            individual[mutate_index] = (0, 1)[individual[mutate_index] == 0]

        def random_selection(population: list[Chromosome]) -> Chromosome:
            """Select and return a random member of the population."""
            return rng.choice(population)

        def tournament_selection(population: list[Chromosome]) -> Chromosome:
            """Select a random number of individuals from the population and
            return the fittest member of them all.
            """
            if self.tournament_size == 0:
                self.tournament_size = 2

            members = rng.sample(population, self.tournament_size)
            return (max if self.maximise_fitness else min)(members, key=attrgetter("fitness"))

        self.fitness_function = None
        self.tournament_selection = tournament_selection
        self.tournament_size = self.population_size // 10
        self.random_selection = random_selection
        self.create_individual = create_individual
        self.crossover_function = crossover
        self.mutate_function = mutate
        self.selection_function = self.tournament_selection

    def create_initial_population(self) -> None:
        """Create members of the first population randomly."""
        initial_population = []
        for _ in range(self.population_size):
            genes = self.create_individual(self.seed_data)
            individual = Chromosome(genes)
            initial_population.append(individual)
        self.current_generation = initial_population

    def calculate_population_fitness(self) -> None:
        """Calculate the fitness of every member of the given population using
        the supplied fitness_function.
        """
        assert self.fitness_function is not None
        for individual in self.current_generation:
            individual.fitness = self.fitness_function(individual.genes, self.seed_data)

    def rank_population(self) -> None:
        """Sort the population by fitness according to the order defined by
        maximise_fitness.
        """
        self.current_generation.sort(key=attrgetter("fitness"), reverse=self.maximise_fitness)

    def create_new_population(self) -> None:
        """Create a new population using the genetic operators (selection,
        crossover, and mutation) supplied.
        """
        new_population: list[Chromosome] = []
        elite = self.current_generation[0]
        selection = self.selection_function

        while len(new_population) < self.population_size:
            parent_1 = copy.copy(selection(self.current_generation))
            parent_2 = copy.copy(selection(self.current_generation))

            child_1, child_2 = parent_1, parent_2
            child_1.fitness, child_2.fitness = 0, 0

            can_crossover = self.random.random() < self.crossover_probability
            can_mutate = self.random.random() < self.mutation_probability

            if can_crossover:
                child_1.genes, child_2.genes = self.crossover_function(list(parent_1.genes), list(parent_2.genes))

            if can_mutate:
                child_1.genes = list(child_1.genes)
                child_2.genes = list(child_2.genes)
                self.mutate_function(child_1.genes)
                self.mutate_function(child_2.genes)

            new_population.append(child_1)
            if len(new_population) < self.population_size:
                new_population.append(child_2)

        if self.elitism:
            new_population[0] = elite

        self.current_generation = new_population

    def create_first_generation(self) -> None:
        """Create the first population, calculate the population's fitness and
        rank the population by fitness according to the order specified.
        """
        self.create_initial_population()
        self.calculate_population_fitness()
        self.rank_population()

    def create_next_generation(self) -> None:
        """Create subsequent populations, calculate the population fitness and
        rank the population by fitness in the order specified.
        """
        self.create_new_population()
        self.calculate_population_fitness()
        self.rank_population()

    def run(self) -> None:
        """Run (solve) the Genetic Algorithm."""
        self.create_first_generation()

        for _ in range(1, self.generations):
            self.create_next_generation()

    def best_individual(self) -> tuple[Fitness, Genes]:
        """Return the individual with the best fitness in the current
        generation.
        """
        best = self.current_generation[0]
        return (best.fitness, best.genes)

    def last_generation(self) -> typing.Iterable[tuple[Fitness, Genes]]:
        """Return members of the last generation as a generator function."""
        return ((member.fitness, member.genes) for member in self.current_generation)


class Chromosome:
    """Chromosome class that encapsulates an individual's fitness and solution
    representation.
    """

    def __init__(self, genes: Genes):
        """Initialise the Chromosome."""
        self.genes = genes
        self.fitness = 0.0

    def __repr__(self) -> str:
        """Return initialised Chromosome representation in human readable form."""
        return repr((self.fitness, self.genes))
