from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

from Cython.Build import cythonize
from setuptools import Command, Extension, setup
from setuptools.command.build import build


class CopyReadmeCommand(Command):
    """Custom build command."""

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        parent = Path(__file__).parent

        shutil.copy2(parent.joinpath("README.md"), parent.joinpath("randovania", "data", "README.md"))


class CustomBuild(build):
    sub_commands = [
        ("copy_readme", None),
        *build.sub_commands,
    ]


ext_modules = None

if os.getenv("RANDOVANIA_COMPILE", "0") != "0":
    debug_mode = os.getenv("RANDOVANIA_DEBUG", "0") != "0"

    if sys.platform == "win32":
        # MSVC
        extra_compile_args = [
            "/std:c++20",
            # Cython boilerplate triggers warning "function call missing argument list", unrelated to our code
            "/wd4551",
        ]
        if debug_mode:
            extra_compile_args.extend(["/Od", "/Zi"])  # Disable optimizations, add debug info
    else:
        # GCC/Clang
        extra_compile_args = ["-std=c++20"]
        if debug_mode:
            extra_compile_args.extend(["-g", "-O0", "-fno-omit-frame-pointer"])  # Debug symbols, no optimization

    ext_modules = cythonize(
        [
            Extension(
                "randovania._native",
                sources=["randovania/_native.py"],
                language="c++",
                extra_compile_args=extra_compile_args,
                extra_link_args=["-g"] if debug_mode and sys.platform != "win32" else [],
            ),
        ],
        annotate=True,
        gdb_debug=debug_mode,  # Add Cython debugging support
    )

setup(
    ext_modules=ext_modules,
    cmdclass={
        "copy_readme": CopyReadmeCommand,
        "build": CustomBuild,
    },
)
