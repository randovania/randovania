from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

from Cython.Build import cythonize
from setuptools import Command, Extension, setup
from setuptools.command.build import build

should_compile = os.getenv("RANDOVANIA_COMPILE", "0") != "0"


class CopyReadmeCommand(Command):
    """Custom build command."""

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        parent = Path(__file__).parent

        shutil.copy2(parent.joinpath("README.md"), parent.joinpath("randovania", "data", "README.md"))


class DeleteUnknownNativeCommand(Command):
    """Custom build command."""

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        parent = Path(__file__).parent
        root = parent.joinpath("randovania")

        cython_files: list[Path] = []

        for path, dirnames, filenames in root.walk():
            relative = path.relative_to(parent)
            if len(relative.parts) < 2 or relative.parts[1] != "data":
                for file in filenames:
                    if file.endswith((".pyd", ".cpp", ".so")):
                        cython_files.append(relative.joinpath(file))

        for file in cython_files:
            associated_py_file = file.as_posix().split(".", 1)[0] + ".py"
            if not should_compile or associated_py_file not in cythonize_files:
                print("Deleting", file)
                file.unlink()


class CustomBuild(build):
    sub_commands = [
        ("copy_readme", None),
        ("delete_unknown_native", None),
        *build.sub_commands,
    ]


cythonize_files = [
    "randovania/lib/bitmask.py",
    "randovania/game_description/resources/resource_collection.py",
    "randovania/graph/graph_requirement.py",
    "randovania/graph/state_native.py",
    "randovania/resolver/resolver_native.py",
    "randovania/generator/generator_native.py",
]

ext_modules = None

if should_compile:
    debug_mode = os.getenv("RANDOVANIA_DEBUG", "0") != "0"
    profiling_mode = os.getenv("RANDOVANIA_PROFILE", "0") != "0"

    if sys.platform == "win32":
        # MSVC
        extra_compile_args = [
            "/std:c++20",
            "/Zi",  # Generate debug info (PDB)
            # Cython boilerplate triggers warning "function call missing argument list", unrelated to our code
            "/wd4551",
        ]
        extra_link_args = []

        if profiling_mode:
            # Add profiling flags for MSVC
            extra_compile_args.extend(
                [
                    "/O2",  # Optimize for speed (but keep symbols)
                    "/Oy-",  # Disable frame pointer omission
                ]
            )
            extra_link_args.extend(
                [
                    "/DEBUG",  # Generate PDB file
                    "/PROFILE",  # Enable profiling
                ]
            )
        elif debug_mode:
            extra_compile_args.extend(["/Od"])  # Disable optimizations
    else:
        # GCC/Clang
        extra_compile_args = [
            "-std=c++20",
            "-g",  # Debug symbols
        ]
        extra_link_args = ["-g"]

        if profiling_mode:
            # Add profiling flags for GCC/Clang
            extra_compile_args.extend(
                [
                    "-O2",  # Optimize but keep symbols
                    "-fno-omit-frame-pointer",  # Keep frame pointers
                    "-fno-inline-functions",  # Don't inline (for clearer profiling)
                ]
            )
        elif debug_mode:
            extra_compile_args.extend(["-O0", "-fno-omit-frame-pointer"])  # no optimization

    ext_modules = cythonize(
        [
            Extension(
                file.replace("/", ".")[:-3],
                sources=[file],
                language="c++",
                extra_compile_args=extra_compile_args,
                extra_link_args=extra_link_args,
            )
            for file in cythonize_files
        ],
        annotate=True,
        compiler_directives={
            "linetrace": profiling_mode or debug_mode,  # Enable line tracing for profiling
            "profile": profiling_mode,  # Enable profiling hooks
        },
        gdb_debug=debug_mode,  # Add Cython debugging support
        emit_linenums=True,
    )

setup(
    ext_modules=ext_modules,
    cmdclass={
        "copy_readme": CopyReadmeCommand,
        "delete_unknown_native": DeleteUnknownNativeCommand,
        "build": CustomBuild,
    },
)
