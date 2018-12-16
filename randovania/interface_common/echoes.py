import multiprocessing
import traceback
from typing import Callable, Union

from randovania.resolver import generator, debug
from randovania.resolver.layout_description import LayoutDescription
from randovania.resolver.permalink import Permalink


def _generate_layout_worker(output_pipe,
                            permalink: Permalink,
                            debug_level: int):
    try:
        def status_update(message: str):
            output_pipe.send(message)

        debug._DEBUG_LEVEL = debug_level
        layout_description = generator.generate_list(permalink, status_update=status_update)
        output_pipe.send(layout_description)
    except Exception as e:
        traceback.print_exc()
        output_pipe.send(e)


def generate_layout(permalink: Permalink,
                    status_update: Callable[[str], None],
                    ) -> LayoutDescription:
    receiving_pipe, output_pipe = multiprocessing.Pipe(False)

    process = multiprocessing.Process(
        target=_generate_layout_worker,
        args=(output_pipe, permalink, debug._DEBUG_LEVEL)
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
