import multiprocessing
import traceback
from typing import Callable, Union

from randovania.generator import generator
from randovania.layout.layout_description import LayoutDescription
from randovania.layout.permalink import Permalink
from randovania.resolver import debug


def _generate_layout_worker(output_pipe,
                            permalink: Permalink,
                            validate_after_generation: bool,
                            timeout_during_generation: bool,
                            debug_level: int):
    try:
        def status_update(message: str):
            output_pipe.send(message)

        debug.set_level(debug_level)
        extra_args = {}
        if not timeout_during_generation:
            extra_args["timeout"] = None

        layout_description = generator.generate_description(permalink,
                                                            status_update=status_update,
                                                            validate_after_generation=validate_after_generation,
                                                            **extra_args)
        output_pipe.send(layout_description)
    except Exception as e:
        traceback.print_exc()
        output_pipe.send(e)


def generate_layout(permalink: Permalink,
                    status_update: Callable[[str], None],
                    validate_after_generation: bool,
                    timeout_during_generation: bool,
                    ) -> LayoutDescription:
    receiving_pipe, output_pipe = multiprocessing.Pipe(False)

    debug_level = debug.debug_level()
    if not permalink.spoiler:
        debug_level = 0

    process = multiprocessing.Process(
        target=_generate_layout_worker,
        args=(output_pipe, permalink, validate_after_generation, timeout_during_generation, debug_level)
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
