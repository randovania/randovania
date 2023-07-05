import asyncio
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from multiprocessing.connection import Connection
from typing import Callable

import sentry_sdk

from randovania.generator import generator
from randovania.interface_common.options import Options
from randovania.layout.base.dock_rando_configuration import DockRandoMode
from randovania.layout.generator_parameters import GeneratorParameters
from randovania.layout.layout_description import LayoutDescription
from randovania.lib.status_update_lib import ProgressUpdateCallable, ConstantPercentageCallback
from randovania.resolver import debug

export_busy = False


def generate_layout(options: Options,
                    parameters: GeneratorParameters,
                    progress_update: ProgressUpdateCallable,
                    retries: int | None = None,
                    ) -> LayoutDescription:
    """
    Creates a LayoutDescription for the configured permalink
    :param options:
    :param parameters:
    :param progress_update:
    :param retries:
    :return:
    """
    with sentry_sdk.start_transaction(op="task", name="generate_layout") as span:
        games = {preset.game.short_name for preset in parameters.presets}
        span.set_tag("num_worlds", parameters.player_count)
        span.set_tag("game", next(iter(games)) if len(games) == 1 else "cross-game")
        span.set_tag("attempts", retries if retries is not None else generator.DEFAULT_ATTEMPTS)
        span.set_tag("validate_after", options.advanced_validate_seed_after)
        span.set_tag("dock_rando", any(
            preset.configuration.dock_rando.mode == DockRandoMode.DOCKS for preset in parameters.presets
        ))

        try:
            result = generate_in_another_process(
                parameters=parameters,
                status_update=ConstantPercentageCallback(progress_update, -1),
                validate_after_generation=options.advanced_validate_seed_after,
                timeout_during_generation=options.advanced_timeout_during_generation,
                attempts=retries,
            )
            span.set_tag("exception", "none")
            span.set_status("ok")
            return result

        except (asyncio.CancelledError, ConnectionResetError) as err:
            span.set_tag("exception", type(err).__name__)
            span.set_status("cancelled")
            raise

        except Exception as err:
            span.set_tag("exception", type(err).__name__)
            span.set_status("unknown_error")
            raise


def _generate_layout_worker(output_pipe: Connection,
                            debug_level: int,
                            extra_args: dict):
    def status_update(message: str):
        output_pipe.send(message)
        if output_pipe.poll():
            raise RuntimeError(output_pipe.recv())

    debug.set_level(debug_level)
    return asyncio.run(generator.generate_and_validate_description(status_update=status_update, **extra_args))


def generate_in_another_process(parameters: GeneratorParameters,
                                status_update: Callable[[str], None],
                                validate_after_generation: bool,
                                timeout_during_generation: bool,
                                attempts: int | None,
                                ) -> LayoutDescription:
    receiving_pipe, output_pipe = multiprocessing.Pipe(True)

    debug_level = debug.debug_level()
    if not parameters.spoiler:
        debug_level = 0

    def on_done(_):
        output_pipe.send(None)

    with ProcessPoolExecutor(max_workers=1) as executor:
        extra_args = {
            "generator_params": parameters,
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
