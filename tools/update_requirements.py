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
stdout = subprocess.PIPE if is_quiet else None

subprocess.run(
    [
        sys.executable,
        "-m",
        "piptools",
        "compile",
        "--allow-unsafe",
        "--extra=gui,server,test",
        "--strip-extras",
        "--output-file",
        "requirements.txt",
        "tools/requirements/requirements.in",
        "setup.py",
    ],
    env=custom_env,
    check=True,
    cwd=parent,
    stdout=stdout,
    stderr=stdout,
)

subprocess.run(
    [
        sys.executable,
        "-m",
        "piptools",
        "compile",
        "--allow-unsafe",
        "--output-file",
        "requirements-lint.txt",
        "tools/requirements/requirements-lint.in",
    ],
    env=custom_env,
    check=True,
    cwd=parent,
    stdout=stdout,
    stderr=stdout,
)
