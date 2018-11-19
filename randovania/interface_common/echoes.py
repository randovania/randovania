import functools
import multiprocessing
import traceback
from typing import Dict, Callable, Union

from randovania.game_description.data_reader import read_resource_database, read_pickup_database
from randovania.game_description.resources import ResourceDatabase, PickupDatabase
from randovania.games.prime import binary_data

from randovania.resolver import generator, debug
from randovania.resolver.layout_configuration import LayoutConfiguration
from randovania.resolver.layout_description import LayoutDescription


def _generate_layout_worker(output_pipe,
                            data: Dict,
                            seed_number: int,
                            configuration: LayoutConfiguration,
                            debug_level: int):
    try:
        def status_update(message: str):
            output_pipe.send(message)

        debug._DEBUG_LEVEL = debug_level
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
        args=(output_pipe, data, seed_number, configuration, debug._DEBUG_LEVEL)
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


@functools.lru_cache()
def default_prime2_resource_database() -> ResourceDatabase:
    return read_resource_database(binary_data.decode_default_prime2()["resource_database"])


@functools.lru_cache()
def default_prime2_pickup_database() -> PickupDatabase:
    return read_pickup_database(binary_data.decode_default_prime2(),
                                default_prime2_resource_database())
