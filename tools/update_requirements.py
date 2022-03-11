import os
import subprocess
import sys
from pathlib import Path

import piptools

# Just import piptools so the error is a bit cleaner in case it's missing.
assert piptools is not None

this_file = Path(__file__)
parent = this_file.parents[1]

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
        "requirements.in",
        "setup.py",
    ],
    env={
        **os.environ,
        "CUSTOM_COMPILE_COMMAND": "python {}".format(this_file.relative_to(parent).as_posix()),
    },
    check=True,
    cwd=parent,
)
