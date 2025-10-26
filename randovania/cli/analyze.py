from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace, _SubParsersAction

__all__ = ["create_subparsers"]


def run_analysis(args: Namespace) -> None:
    from randovania.log_analyzer import log_analyzer

    log_analyzer.create_report(
        args.seeds_dir, args.output_file, args.csv_dir, args.use_percentage, args.major_progression_only
    )
    print("Analysis finished")


def create_subparsers(sub_parsers: _SubParsersAction) -> None:
    parser: ArgumentParser = sub_parsers.add_parser("analyze", help="Run analysis on generated games.")
    parser.add_argument("--csv-dir", type=Path)
    parser.add_argument("seeds_dir", type=Path)
    parser.add_argument("output_file", type=Path)
    parser.add_argument("--use-percentage", action="store_true")
    parser.add_argument("--major-progression-only", action="store_true")

    parser.set_defaults(func=run_analysis)
