import multiprocessing
import random
from typing import Dict, Optional, NamedTuple, List, Tuple, Set, Callable

from randovania.games.prime import log_parser
from randovania.games.prime.log_parser import RandomizerLog
from randovania.interface_common.options import Options
from randovania.resolver import data_reader, resolver, debug
from randovania.resolver.state import State


class ResolverConfiguration(NamedTuple):
    difficulty: int
    minimum_difficulty: int
    enabled_tricks: Set[int]
    item_loss: bool

    @classmethod
    def from_options(cls, options: Options) -> "ResolverConfiguration":
        return ResolverConfiguration(options.maximum_difficulty,
                                     options.minimum_difficulty,
                                     options.enabled_tricks,
                                     not options.remove_item_loss)


class RandomizerConfiguration(NamedTuple):
    exclude_pickups: List[int]
    randomize_elevators: bool

    @classmethod
    def from_options(cls, options: Options) -> "RandomizerConfiguration":
        return RandomizerConfiguration(list(options.excluded_pickups),
                                       options.randomize_elevators)


def run_resolver(data: Dict,
                 randomizer_log: RandomizerLog,
                 resolver_config: ResolverConfiguration,
                 verbose=True) -> Optional[State]:
    game_description = data_reader.decode_data(data, randomizer_log.pickup_database, randomizer_log.elevators)
    final_state = resolver.resolve(resolver_config.difficulty,
                                   resolver_config.enabled_tricks,
                                   resolver_config.item_loss, game_description)
    if final_state:
        if resolver_config.minimum_difficulty > 0:
            if resolver.resolve(resolver_config.minimum_difficulty - 1,
                                resolver_config.enabled_tricks,
                                resolver_config.item_loss,
                                game_description):
                if verbose:
                    print("Game is beatable using a lower difficulty!")
                return None

        if verbose:
            print("Game is possible!")

        item_percentage = final_state.resources.get(game_description.resource_database.item_percentage(), 0)
        if verbose:
            print("Victory with {}% of the items.".format(item_percentage))
    return final_state


def print_path_for_state(final_state):
    states = []
    state = final_state
    while state:
        states.append(state)
        state = state.previous_state
    print("Path taken:")
    for state in reversed(states):
        print("> {}".format(debug.n(state.node, with_world=True)))


def generate_and_validate(data: Dict,
                          randomizer_config: RandomizerConfiguration,
                          resolver_config: ResolverConfiguration,
                          input_queue: multiprocessing.Queue,
                          output_queue: multiprocessing.Queue):
    while True:
        seed = input_queue.get()
        randomizer_log = log_parser.generate_log(seed,
                                                 randomizer_config.exclude_pickups,
                                                 randomizer_config.randomize_elevators)

        final_state = run_resolver(data=data,
                                   randomizer_log=randomizer_log,
                                   resolver_config=resolver_config,
                                   verbose=False)
        output_queue.put((seed, final_state))


def search_seed(data: Dict,
                randomizer_config: RandomizerConfiguration,
                resolver_config: ResolverConfiguration,
                cpu_count: int,
                seed_report: Callable[[int], None],
                start_on_seed: Optional[int] = None) -> Tuple[int, int]:
    input_queue = multiprocessing.Queue()
    output_queue = multiprocessing.Queue()

    process_list = [
        multiprocessing.Process(
            target=generate_and_validate,
            args=(data, randomizer_config, resolver_config, input_queue, output_queue)
        )
        for _ in range(cpu_count)
    ]

    initial_seed = start_on_seed
    if initial_seed is None:
        initial_seed = random.randint(0, 2147483647)
    seed_count = 0

    def generate_seed():
        nonlocal seed_count
        seed_count += 1
        new_seed = initial_seed + seed_count
        if new_seed > 2147483647:
            new_seed -= 2147483647
        return new_seed

    for _ in range(cpu_count):
        input_queue.put_nowait(generate_seed())

    for process in process_list:
        process.start()
    try:
        while True:
            seed, valid = output_queue.get()
            if valid:
                break
            else:
                seed_report(seed_count)
                input_queue.put_nowait(generate_seed())

    finally:
        for process in process_list:
            process.terminate()

    return seed, seed_count


def search_seed_with_options(data: Dict,
                             options: Options,
                             seed_report: Callable[[int], None],
                             start_on_seed: Optional[int] = None) -> Tuple[int, int]:

    randomizer_config = RandomizerConfiguration.from_options(options)
    resolver_config = ResolverConfiguration.from_options(options)
    cpu_count = options.cpu_usage.num_cpu_for_count(multiprocessing.cpu_count())
    return search_seed(data=data,
                       randomizer_config=randomizer_config,
                       resolver_config=resolver_config,
                       cpu_count=cpu_count,
                       seed_report=seed_report,
                       start_on_seed=start_on_seed)
