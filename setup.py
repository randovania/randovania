from __future__ import annotations

import os

from mypyc.build import mypycify
from setuptools import setup
from setuptools.command.build_py import build_py
from wheel.bdist_wheel import bdist_wheel

try:
    from pyqt_distutils.build_ui import build_ui
except ModuleNotFoundError:
    build_ui = None


class BuildPyCommand(build_py):
    def run(self):
        self.run_command("build_ui")
        super().run()


class BDistWheelCommand(bdist_wheel):
    def run(self):
        self.run_command("build_ui")
        super().run()


ext_modules = None

if not bool(int(os.getenv("RANDOVANIA_SKIP_COMPILE", "0"))):
    ext_modules = mypycify(
        [
            "randovania/game_description/requirements/",
        ]
    )


setup(
    ext_modules=ext_modules,
    cmdclass={
        "build_ui": build_ui,
        "build_py": BuildPyCommand,
        "bdist_wheel": BDistWheelCommand,
    },
)
