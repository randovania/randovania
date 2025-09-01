from __future__ import annotations

import shutil
from pathlib import Path

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


class CustomBuild(build):
    sub_commands = [
        ("copy_readme", None),
        *build.sub_commands,
    ]


setup(
    cmdclass={
        "copy_readme": CopyReadmeCommand,
        "build": CustomBuild,
    },
)
