import argparse
import pathlib
import subprocess

parser = argparse.ArgumentParser()
extras_group = parser.add_mutually_exclusive_group()
extras_group.add_argument("--thin", action="store_true")
extras_group.add_argument("--full", action="store_true")
native_group = parser.add_mutually_exclusive_group()
native_group.add_argument("--native", action="store_true", help="Requests that native code is compiled.")
native_group.add_argument("--pure", action="store_true", help="Use the pure python mode. Default.")
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

enable_file = pathlib.Path("randovania/enable-cython")
if args.pure:
    enable_file.unlink(missing_ok=True)
else:
    enable_file.write_bytes(b"")

try:
    subprocess.run(
        # Using frozen instead of locked to not fail for more casual users and to not modify the uv.lock for them too
        ["uv", "sync", "--frozen", *extra],
        check=True,
    )

    subprocess.run(["uvx", "pre-commit", "install"], check=False)

    print("Setup finished successfully.")

except subprocess.CalledProcessError as e:
    raise SystemExit(e.returncode)
