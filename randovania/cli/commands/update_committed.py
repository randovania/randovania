from __future__ import annotations

import asyncio
import subprocess
import sys
from argparse import Namespace
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from argparse import ArgumentParser, _SubParsersAction

_REPO_ROOT = Path(__file__).parents[3]


def _run_acceptance_tests(*extra_args: str) -> int:
    command = [sys.executable, "-m", "pytest", "-n", "auto", "-m", "acceptance", *extra_args]
    return subprocess.run(command, cwd=_REPO_ROOT, check=False).returncode


def update_acceptance_tests_command_logic(args: Namespace) -> int:
    print("Rewriting the reference files of all acceptance tests...", flush=True)
    if _run_acceptance_tests("--update-committed") != 0:
        return 1

    # A rewritten reference file can be the input of another acceptance test, and xdist gives no ordering between them.
    print("Verifying the rewritten reference files...", flush=True)
    return _run_acceptance_tests()


def update_committed_command_logic(args: Namespace) -> int:
    from randovania.cli.commands.expected_seed_hash import update_expected_seed_hash_logic
    from randovania.cli.database import refresh_game_description_logic, refresh_pickup_database_logic

    refresh_args = Namespace(game=None, integrity_check=False)

    print("Refreshing all logic databases...", flush=True)
    refresh_game_description_logic(refresh_args)

    print("Refreshing all pickup databases...", flush=True)
    refresh_pickup_database_logic(refresh_args)

    # Omitted because migrating every committed preset to the latest schema is a large diff of its own.
    # Run `randovania development refresh-presets` when that migration is what you actually want.
    # refresh_presets_command_logic(refresh_args)

    print("Updating the expected seed hash of all games...", flush=True)
    asyncio.run(update_expected_seed_hash_logic(Namespace(games=[])))

    return update_acceptance_tests_command_logic(args)


def add_update_acceptance_tests_command(sub_parsers: _SubParsersAction) -> None:
    parser: ArgumentParser = sub_parsers.add_parser(
        "update-acceptance-tests",
        help="Rewrites and verifies the committed reference files of all acceptance tests.",
    )

    parser.set_defaults(func=update_acceptance_tests_command_logic)


def add_update_committed_command(sub_parsers: _SubParsersAction) -> None:
    parser: ArgumentParser = sub_parsers.add_parser(
        "update-committed",
        help="Regenerates every committed file that Randovania generates: databases and test reference files.",
    )

    parser.set_defaults(func=update_committed_command_logic)
