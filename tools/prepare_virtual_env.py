import argparse
import pathlib
import subprocess

parser = argparse.ArgumentParser()
group = parser.add_mutually_exclusive_group()
group.add_argument("--thin", action="store_true")
group.add_argument("--full", action="store_true")
args = parser.parse_args()

if args.full:
    extra = ["--all-extras", "--all-groups"]
else:
    extra = ["--extra", "gui"]

if not pathlib.Path(".git").is_dir():
    print("""
Downloading Randovania via the "Download ZIP" button in GitHub is not supported.

Please follow the instructions in the README:
    https://github.com/randovania/randovania/blob/main/README.md#installation
""")
    raise SystemExit(1)

try:
    subprocess.run(
        [
            "uv",
            "sync",
            "--frozen",
            *extra,
        ],
        check=True,
    )

    subprocess.run(["uvx", "pre-commit", "install"], check=False)

    print("Setup finished successfully.")

except subprocess.CalledProcessError as e:
    raise SystemExit(e.returncode)
