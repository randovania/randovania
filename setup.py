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
    profiling_mode = os.getenv("RANDOVANIA_PROFILE", "0") != "0"

    if sys.platform == "win32":
        # MSVC
        extra_compile_args = [
            "/std:c++20",
            # Cython boilerplate triggers warning "function call missing argument list", unrelated to our code
            "/wd4551",
        ]
        extra_link_args = []

        if profiling_mode:
            # Add profiling flags for MSVC
            extra_compile_args.extend(
                [
                    "/Zi",  # Generate debug info (PDB)
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
            extra_compile_args.extend(["/Od", "/Zi"])  # Disable optimizations, add debug info
    else:
        # GCC/Clang
        extra_compile_args = ["-std=c++20"]
        extra_link_args = []

        if profiling_mode:
            # Add profiling flags for GCC/Clang
            extra_compile_args.extend(
                [
                    "-g",  # Debug symbols
                    "-O2",  # Optimize but keep symbols
                    "-fno-omit-frame-pointer",  # Keep frame pointers
                    "-fno-inline-functions",  # Don't inline (for clearer profiling)
                ]
            )
            extra_link_args.append("-g")
        elif debug_mode:
            extra_compile_args.extend(["-g", "-O0", "-fno-omit-frame-pointer"])  # Debug symbols, no optimization
            extra_link_args.append("-g")

    ext_modules = cythonize(
        [
            Extension(
                "randovania.lib.bitmask",
                sources=["randovania/lib/bitmask.py"],
                language="c++",
                extra_compile_args=extra_compile_args,
                extra_link_args=extra_link_args,
            ),
            Extension(
                "randovania.game_description.resources.resource_collection",
                sources=["randovania/game_description/resources/resource_collection.py"],
                language="c++",
                extra_compile_args=extra_compile_args,
                extra_link_args=extra_link_args,
            ),
            Extension(
                "randovania.graph.graph_requirement",
                sources=["randovania/graph/graph_requirement.py"],
                language="c++",
                extra_compile_args=extra_compile_args,
                extra_link_args=extra_link_args,
            ),
            Extension(
                "randovania.graph.state_native",
                sources=["randovania/graph/state_native.py"],
                language="c++",
                extra_compile_args=extra_compile_args,
                extra_link_args=extra_link_args,
            ),
            Extension(
                "randovania.resolver.resolver_native",
                sources=["randovania/resolver/resolver_native.py"],
                language="c++",
                extra_compile_args=extra_compile_args,
                extra_link_args=extra_link_args,
            ),
            Extension(
                "randovania.generator.generator_native",
                sources=["randovania/generator/generator_native.py"],
                language="c++",
                extra_compile_args=extra_compile_args,
                extra_link_args=extra_link_args,
            ),
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
        "build": CustomBuild,
    },
)
