import argparse
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--git-add", action="store_true")
    parser.add_argument("--all-ui-files", action="store_true")
    parser.add_argument("--fail-on-difference", action="store_true")
    parser.add_argument("paths", type=Path, nargs="+")
    args = parser.parse_args()
    paths: list[Path] = args.paths
    new_paths: list[str] = []

    import PySide6

    if args.all_ui_files:
        paths_to_glob = []
        for path in list(paths):
            if path.is_dir():
                paths_to_glob.append(path)
                paths.remove(path)

        for path in paths_to_glob:
            paths += list(path.rglob("*.ui"))

    try:

        def process_file(path: Path) -> None:
            new_file = path.parents[1].joinpath("generated").joinpath(path.stem + "_ui.py")
            new_paths.append(os.fspath(new_file))
            result = subprocess.run(
                [
                    "pyside6-uic",
                    "--absolute-imports",
                    os.fspath(path),
                ],
                stdout=subprocess.PIPE,
                check=True,
            )
            new_content = result.stdout.replace(
                b"Qt User Interface Compiler version " + PySide6.__version__.encode(), b"tools/uic_wrapper.py"
            )
            new_file.write_bytes(new_content)

        with ThreadPoolExecutor() as executor:
            for path_to_process in paths:
                executor.submit(process_file, path_to_process).add_done_callback(lambda f: f.result())

        if args.fail_on_difference:
            print(">> Checking for any modified files.")
            subprocess.check_call(["git", "diff", "--exit-code"])

        if args.git_add:
            subprocess.check_call(
                ["git", "add"] + new_paths,
            )
    except subprocess.CalledProcessError as e:
        print("!! An error has occurred!")
        raise SystemExit(e.returncode)


if __name__ == "__main__":
    main()
