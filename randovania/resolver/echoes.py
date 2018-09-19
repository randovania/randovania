import multiprocessing
import random
import traceback
from typing import Dict, Optional, NamedTuple, List, Tuple, Set, Callable, Union

from randovania.games.prime import log_parser
from randovania.games.prime.log_parser import RandomizerLog
from randovania.resolver import data_reader, resolver, debug, generator
from randovania.resolver.game_patches import GamePatches
from randovania.resolver.layout_configuration import LayoutConfiguration, LayoutDifficulty, LayoutEnabledFlag, \
    LayoutRandomizedFlag, LayoutMode, LayoutLogic
from randovania.resolver.layout_description import LayoutDescription
from randovania.resolver.node import EventNode, PickupNode
from randovania.resolver.resources import PickupIndex
from randovania.resolver.state import State


class ResolverConfiguration(NamedTuple):
    difficulty: int
    minimum_difficulty: int
    enabled_tricks: Set[int]
    item_loss: bool


class RandomizerConfiguration(NamedTuple):
    exclude_pickups: List[int]
    randomize_elevators: bool


def run_resolver(data: Dict,
                 randomizer_log: RandomizerLog,
                 resolver_config: ResolverConfiguration,
                 verbose=True) -> Optional[State]:
    game_description = data_reader.decode_data(data, randomizer_log.elevators)
    game_patches = GamePatches(resolver_config.item_loss, randomizer_log.pickup_mapping)

    configuration = LayoutConfiguration(logic=LayoutLogic.NO_GLITCHES,
                                        mode=LayoutMode.STANDARD,
                                        sky_temple_keys=LayoutRandomizedFlag.RANDOMIZED,
                                        item_loss=LayoutEnabledFlag.ENABLED,
                                        elevators=LayoutRandomizedFlag.VANILLA,
                                        hundo_guaranteed=LayoutEnabledFlag.DISABLED,
                                        difficulty=LayoutDifficulty.NORMAL)

    final_state = resolver.resolve(
        resolver_config.difficulty,
        resolver_config.enabled_tricks,
        configuration,
        game_description,
        game_patches)
    if final_state:
        if resolver_config.minimum_difficulty > 0:
            if resolver.resolve(resolver_config.minimum_difficulty - 1, resolver_config.enabled_tricks,
                                configuration, game_description, game_patches):
                if verbose:
                    print("Game is beatable using a lower difficulty!")
                return None

        if verbose:
            print("Game is possible!")

        item_percentage = final_state.resources.get(game_description.resource_database.item_percentage(), 0)
        if verbose:
            print("Victory with {}% of the items.".format(item_percentage))
    return final_state


def print_path_for_state(final_state: State,
                         patches: GamePatches,
                         include_inner_steps: bool,
                         include_picked_item: bool):
    states = []
    state = final_state
    while state:
        states.append(state)
        state = state.previous_state

    print("Path taken:")
    for state in reversed(states):
        if include_inner_steps and state.path_from_previous_state:
            print(" * {}".format(
                "\n * ".join(
                    debug.n(node) for node in state.path_from_previous_state
                    if node is not state.previous_state.node
                )
            ))

        extra_text = ""
        if include_picked_item:
            if isinstance(state.node, (EventNode, PickupNode)):
                resource = state.node.resource(state.resource_database)
                if isinstance(resource, PickupIndex):
                    mapping = patches.pickup_mapping[resource.index]
                    if mapping is not None:
                        resource = state.resource_database.pickups[mapping]
                    else:
                        resource = None
                extra_text = " for {}".format(resource)
        print("> {}{}".format(debug.n(state.node, with_world=True), extra_text))


def generate_and_validate(data: Dict,
                          randomizer_config: RandomizerConfiguration,
                          resolver_config: ResolverConfiguration,
                          input_queue: multiprocessing.Queue,
                          output_queue: multiprocessing.Queue):
    while True:
        seed = input_queue.get()
        if seed is None:
            raise RuntimeError("generate_and_validate got None from input queue")
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

    next_seed = start_on_seed
    if next_seed is None:
        next_seed = random.randint(0, 2147483647)

    def generate_seed():
        nonlocal next_seed
        new_seed = next_seed
        next_seed += 1
        if next_seed > 2147483647:
            next_seed -= 2147483647
        return new_seed

    for _ in range(cpu_count):
        input_queue.put_nowait(generate_seed())

    for process in process_list:
        process.start()
    try:
        seed_count = 0
        while True:
            seed, valid = output_queue.get()
            seed_count += 1
            if valid:
                break
            else:
                seed_report(seed_count)
                input_queue.put_nowait(generate_seed())

    finally:
        for process in process_list:
            process.terminate()

    return seed, seed_count


def _generate_layout_worker(output_pipe,
                            data: Dict,
                            seed_number: int,
                            configuration: LayoutConfiguration):
    try:
        def status_update(message: str):
            output_pipe.send(message)

        layout_description = generator.generate_list(data,
                                                     seed_number,
                                                     configuration,
                                                     status_update=status_update)
        output_pipe.send(layout_description)
    except Exception as e:
        traceback.print_exc()
        output_pipe.send(e)


def generate_layout(data: Dict,
                    seed_number: int,
                    configuration: LayoutConfiguration,
                    status_update: Callable[[str], None]
                    ) -> LayoutDescription:
    receiving_pipe, output_pipe = multiprocessing.Pipe(False)

    process = multiprocessing.Process(
        target=_generate_layout_worker,
        args=(output_pipe, data, seed_number, configuration)
    )
    process.start()
    try:
        result: Union[Exception, LayoutDescription] = None
        while result is None:
            pipe_input = receiving_pipe.recv()
            if isinstance(pipe_input, (LayoutDescription, Exception)):
                result = pipe_input
            else:
                status_update(pipe_input)
    finally:
        process.terminate()

    if isinstance(result, Exception):
        raise result
    else:
        return result
