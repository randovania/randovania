import os
import subprocess
import sys
from pathlib import Path

import piptools

# Just import piptools so the error is a bit cleaner in case it's missing.
assert piptools is not None

this_file = Path(__file__)
parent = this_file.parents[1]
custom_env = {
    **os.environ,
    "CUSTOM_COMPILE_COMMAND": "python {}".format(this_file.relative_to(parent).as_posix()),
}

is_quiet = "--quiet" in sys.argv
upgrade_arg = ["--upgrade"] if ("--upgrade" in sys.argv) else []
stdout = subprocess.PIPE if is_quiet else None


def print_arguments(args):
    args = [
        sys.executable,
        "-m",
        "piptools",
        "compile",
        "--allow-unsafe",
        "--resolver", "backtracking",
        *args,
    ]
    print("Running {}".format(" ".join(args)))
    return args


subprocess.run(
    print_arguments([
        "--extra=gui,server,test",
        "--strip-extras",
        "--output-file",
        "requirements.txt",
        *upgrade_arg,
        "tools/requirements/requirements.in",
        "setup.py",
    ]),
    env=custom_env,
    check=True,
    cwd=parent,
    stdout=stdout,
    stderr=stdout,
)

subprocess.run(
    print_arguments([
        "--output-file",
        "requirements-lint.txt",
        *upgrade_arg,
        "tools/requirements/requirements-lint.in",
    ]),
    env=custom_env,
    check=True,
    cwd=parent,
    stdout=stdout,
    stderr=stdout,
)
