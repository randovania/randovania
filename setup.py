from __future__ import annotations

from setuptools import setup
from setuptools.command.build import build

try:
    from pyqt_distutils.build_ui import build_ui
except ModuleNotFoundError:
    build_ui = None


class CustomBuild(build):
    sub_commands = [("build_ui", None), *build.sub_commands]


setup(
    cmdclass={
        "build_ui": build_ui,
        "build": CustomBuild,
    },
)
