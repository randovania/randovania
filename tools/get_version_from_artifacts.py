"""Helper for finding Randovania version out of a directory with release artifacts. Used by CI."""

import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact_dir", type=Path)
    args = parser.parse_args()

    artifact_dir: Path = args.artifact_dir
    versions = {file.name.split("-")[1] for file in artifact_dir.glob("randovania-*")}
    if len(versions) != 1:
        raise ValueError(f"Found versions {sorted(versions)} in {artifact_dir}, expected just one")

    print(list(versions)[0])


if __name__ == "__main__":
    main()
