import multiprocessing
import traceback
from typing import Dict, Callable, Union

from randovania.resolver import generator
from randovania.resolver.layout_configuration import LayoutConfiguration
from randovania.resolver.layout_description import LayoutDescription


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
