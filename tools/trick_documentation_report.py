import os
import subprocess
import sys
import tempfile
from pathlib import Path

from randovania.games.game import RandovaniaGame


def post_report(report: dict[RandovaniaGame, tuple[int, int]], webhook_url: str) -> None:
    this_dir = Path(__file__).parent

    args = [
        sys.executable,
        os.fspath(this_dir.joinpath("send_report_to_discord.py")),
        "--webhook",
        webhook_url,
        "--title",
        "Trick documentation report",
    ]

    for game, (documented, total) in report.items():
        percent = int((documented / total) * 100)
        game_name = game.long_name.replace(":", "@")
        args.extend(
            [
                "--field",
                f"{game_name}:{percent: >3}% ({documented} out of {total})",
            ]
        )

    subprocess.run(args, check=True)


def main() -> None:
    reports = {}

    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)

        for game_enum in RandovaniaGame.sorted_all_games():
            game = game_enum.value
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "randovania",
                    "database",
                    "--game",
                    game,
                    "trick-usage-documentation",
                    os.fspath(root.joinpath(f"{game}.txt")),
                ],
                check=True,
                text=True,
            )

            total = 0
            documented = 0

            with root.joinpath(f"{game}.txt").open() as usage_file:
                for line in usage_file:
                    if line.startswith("- ["):
                        total += 1
                        if line.startswith("- [X]"):
                            documented += 1

            reports[game_enum] = (documented, total)

    try:
        webhook_url = os.environ["WEBHOOK_URL"]
    except KeyError:
        return

    post_report(reports, webhook_url)


if __name__ == "__main__":
    main()
