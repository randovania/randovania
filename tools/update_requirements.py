from __future__ import annotations

import os
import subprocess
import sys
import tomllib
from pathlib import Path

import piptools

# Just import piptools so the error is a bit cleaner in case it's missing.
assert piptools is not None

this_file = Path(__file__)
parent = this_file.parents[1]
custom_env = {
    **os.environ,
    "UV_CUSTOM_COMPILE_COMMAND": f"python {this_file.relative_to(parent).as_posix()}",
}

is_quiet = "--quiet" in sys.argv
upgrade_arg = ["--upgrade"] if ("--upgrade" in sys.argv) else []
stdout = subprocess.PIPE if is_quiet else None

# Create requirements-setuptools.in
pyproject = tomllib.loads(parent.joinpath("pyproject.toml").read_text())
parent.joinpath("tools/requirements/requirements-setuptools.in").write_text(
    "\n".join(
        pyproject["build-system"]["requires"]
        + [
            "build",
            "pyinstaller",
            "pyinstaller-hooks-contrib",
            "-c ../../requirements.txt",
        ]
    )
)


def print_arguments(args):
    args = [
        sys.executable,
        "-m",
        "piptools",
        "compile",
        "--allow-unsafe",
        "--resolver",
        "backtracking",
        *args,
    ]
    print("Running {}".format(" ".join(args)))
    return args


def run_compile(
    output_file: str,
    custom_args,
    extra: list[str] | None = None,
):
    args = [
        "uv",
        "pip",
        "compile",
        "--universal",
        "--strip-extras",
        "--output-file",
        output_file,
        *upgrade_arg,
    ]
    for e in extra or []:
        args.extend(["--extra", e])
    args.extend(custom_args)

    print("Running {}".format(" ".join(args)))
    subprocess.run(
        args,
        env=custom_env,
        check=True,
        cwd=parent,
        stdout=stdout,
        stderr=stdout,
    )
    final_file = parent.joinpath(output_file)
    output_contents = final_file.read_text()

    def fix_file(contents: str) -> str:
        return contents.replace(
            os.fspath(parent.joinpath("requirements.txt")), "requirements.txt"
        ).replace(
            "tools/requirements/../../requirements.txt", "requirements.txt"
        )

    final_file.write_text(fix_file(output_contents))


run_compile(
    "requirements.txt",
    [
        "setup.py",
    ],
    extra=["gui", "exporters", "server", "test", "typing", "website"],
)

run_compile(
    "requirements-setuptools.txt",
    [
        "tools/requirements/requirements-setuptools.in",
    ],
)

run_compile(
    "requirements-lint.txt",
    [
        "tools/requirements/requirements-lint.in",
    ],
)
