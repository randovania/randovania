from __future__ import annotations

import os
import shutil
from pathlib import Path

from mypyc.build import mypycify
from setuptools import Command, setup
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


ext_modules = None

if os.getenv("RANDOVANIA_COMPILE", "0") != "0":
    ext_modules = mypycify(
        [
            "randovania/game_description/requirements/",
        ]
    )


class CustomBuild(build):
    sub_commands = [
        ("copy_readme", None),
        *build.sub_commands,
    ]


setup(
    ext_modules=ext_modules,
    cmdclass={
        "copy_readme": CopyReadmeCommand,
        "build": CustomBuild,
    },
)
