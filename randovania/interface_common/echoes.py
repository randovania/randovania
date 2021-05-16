import asyncio
import multiprocessing
from concurrent.futures.process import ProcessPoolExecutor
from multiprocessing.connection import Connection
from typing import Callable, Optional

from randovania.generator import generator
from randovania.layout.layout_description import LayoutDescription
from randovania.layout.permalink import Permalink
from randovania.resolver import debug


def _generate_layout_worker(output_pipe: Connection,
                            debug_level: int,
                            extra_args: dict):
    def status_update(message: str):
        output_pipe.send(message)
        if output_pipe.poll():
            raise RuntimeError(output_pipe.recv())

    debug.set_level(debug_level)
    return asyncio.run(generator.generate_and_validate_description(status_update=status_update, **extra_args))


def generate_description(permalink: Permalink,
                         status_update: Callable[[str], None],
                         validate_after_generation: bool,
                         timeout_during_generation: bool,
                         attempts: Optional[int],
                         ) -> LayoutDescription:
    receiving_pipe, output_pipe = multiprocessing.Pipe(True)

    debug_level = debug.debug_level()
    if not permalink.spoiler:
        debug_level = 0

    def on_done(_):
        output_pipe.send(None)

    with ProcessPoolExecutor(max_workers=1) as executor:
        extra_args = {
            "permalink": permalink,
            "validate_after_generation": validate_after_generation,
        }
        if not timeout_during_generation:
            extra_args["timeout"] = None
        if attempts is not None:
            extra_args["attempts"] = attempts

        future = executor.submit(_generate_layout_worker, output_pipe, debug_level, extra_args)
        future.add_done_callback(on_done)

        while not future.done():
            message = receiving_pipe.recv()
            if message is not None:
                try:
                    status_update(message)
                except Exception:
                    receiving_pipe.send("close")
                    raise

        return future.result()
