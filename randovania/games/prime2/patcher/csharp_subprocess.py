from __future__ import annotations

import asyncio
import os
import platform
import re
from asyncio import IncompleteReadError, StreamReader, StreamWriter
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from os import _Environ

IO_LOOP: asyncio.AbstractEventLoop | None = None


def is_windows() -> bool:
    return platform.system() == "Windows"


def is_mac() -> bool:
    return platform.system() == "Darwin"


async def _write_data(stream: StreamWriter, data: str):
    stream.write(data.encode("UTF-8"))
    stream.close()


async def _read_data(stream: StreamReader, read_callback: Callable[[str], None]):
    while True:
        try:
            line = await stream.readuntil(b"\r")
        except IncompleteReadError as incomplete:
            line = incomplete.partial
        if line:
            try:
                decoded = line.decode()
            except UnicodeDecodeError:
                decoded = line.decode("latin1")
            for x in re.split(r"[\r\n]", decoded.strip()):
                if x:
                    read_callback(x)
        else:
            break


async def _process_command_async(args: list[str], input_data: str, read_callback: Callable[[str], None],
                                 envs: _Environ | dict = os.environ):
    process = await asyncio.create_subprocess_exec(*args,
                                                   stdin=asyncio.subprocess.PIPE,
                                                   stdout=asyncio.subprocess.PIPE,
                                                   stderr=asyncio.subprocess.STDOUT,
                                                   env=envs)

    await asyncio.gather(
        _write_data(process.stdin, input_data),
        _read_data(process.stdout, read_callback),
    )
    await process.wait()


def process_command(args: list[str], input_data: str, read_callback: Callable[[str], None],
                    add_mono_if_needed: bool = True):
    if not Path(args[0]).is_file():
        raise FileNotFoundError(f"{args[0]} not found")

    envs = os.environ
    if add_mono_if_needed and not is_windows():
        args = ["mono", *args]
        # Add common Mono paths to PATH, as they aren't there by default
        if is_mac():
            envs = envs.copy()
            envs["PATH"] = (f"{envs['PATH']}:"
                            "/Library/Frameworks/Mono.framework/Versions/Current/Commands:"
                            "/usr/local/bin:"
                            "/opt/homebrew/bin")

    work = _process_command_async(args, input_data, read_callback, envs)

    if IO_LOOP is None:
        if is_windows():
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        asyncio.run(work)
    else:
        asyncio.run_coroutine_threadsafe(work, IO_LOOP).result()
