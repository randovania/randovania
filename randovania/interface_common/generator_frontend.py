from __future__ import annotations

import asyncio
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from typing import TYPE_CHECKING

from randovania import monitoring
from randovania.generator import generator
from randovania.interface_common.preset_manager import PresetManager
from randovania.layout.base.dock_rando_configuration import DockRandoMode
from randovania.lib.status_update_lib import ConstantPercentageCallback, ProgressUpdateCallable
from randovania.resolver import debug

if TYPE_CHECKING:
    from collections.abc import Callable
    from multiprocessing.connection import Connection

    from randovania.interface_common.options import Options
    from randovania.layout.generator_parameters import GeneratorParameters
    from randovania.layout.layout_description import LayoutDescription

export_busy = False


def generate_layout(
    options: Options,
    parameters: GeneratorParameters,
    progress_update: ProgressUpdateCallable,
    retries: int | None = None,
    world_names: list[str] | None = None,
) -> LayoutDescription:
    """
    Creates a LayoutDescription for the configured permalink
    :param options:
    :param parameters:
    :param progress_update:
    :param retries:
    :param world_names:
    :return:
    """
    with monitoring.start_transaction(op="task", name="generate_layout") as span:
        games = {preset.game.short_name for preset in parameters.presets}
        span.set_tag("num_worlds", parameters.world_count)
        span.set_tag("game", next(iter(games)) if len(games) == 1 else "cross-game")
        span.set_tag("amount_of_games", len(games))
        span.set_tag("unique_games", sorted(set(games)))
        span.set_tag("attempts", retries if retries is not None else generator.DEFAULT_ATTEMPTS)
        span.set_tag("validate_after", options.advanced_validate_seed_after)
        span.set_tag(
            "dock_rando",
            any(preset.configuration.dock_rando.mode == DockRandoMode.DOCKS for preset in parameters.presets),
        )
        span.set_tag(
            "minimal_logic", any(preset.configuration.trick_level.minimal_logic for preset in parameters.presets)
        )
        if len(games) == 1:
            manager = PresetManager(None)
            preset = parameters.get_preset(0)
            if manager.is_included_preset_uuid(preset.uuid):
                span.set_tag("builtin_preset", f"{preset.name} ({preset.game.short_name})")

        extra_args = {
            "generator_params": parameters,
            "validate_after_generation": options.advanced_validate_seed_after,
            "world_names": world_names,
        }
        if not options.advanced_timeout_during_generation:
            extra_args["timeout"] = None
        if retries is not None:
            extra_args["attempts"] = retries

        debug_level = debug.debug_level()
        if not parameters.spoiler:
            debug_level = 0

        if options.advanced_generate_in_another_process:
            generator_function = generate_in_another_process
        else:
            generator_function = generate_in_host_process

        try:
            result = generator_function(
                status_update=ConstantPercentageCallback(progress_update, -1),
                debug_level=debug_level,
                extra_args=extra_args,
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


def _generate_layout_worker(output_pipe: Connection, debug_level: int, extra_args: dict):
    def status_update(message: str):
        output_pipe.send(message)
        if output_pipe.poll():
            raise RuntimeError(output_pipe.recv())

    debug.set_level(debug_level)
    return asyncio.run(generator.generate_and_validate_description(status_update=status_update, **extra_args))


def generate_in_another_process(
    status_update: Callable[[str], None],
    debug_level: int,
    extra_args: dict,
) -> LayoutDescription:
    receiving_pipe, output_pipe = multiprocessing.Pipe(True)

    def on_done(_):
        output_pipe.send(None)

    with ProcessPoolExecutor(max_workers=1) as executor:
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


def generate_in_host_process(
    status_update: Callable[[str], None],
    debug_level: int,
    extra_args: dict,
) -> LayoutDescription:
    with debug.with_level(debug_level):
        return asyncio.run(
            generator.generate_and_validate_description(
                **extra_args,
                status_update=status_update,
            )
        )
