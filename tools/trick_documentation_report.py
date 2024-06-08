import argparse
import asyncio
import os
import shutil
import subprocess
import sys
import typing
from pathlib import Path

import aiohttp
import discord

import randovania
from randovania.games.game import RandovaniaGame


class TrickDocumentation(typing.NamedTuple):
    documented: int
    undocumented: int
    skipped: int


async def post_report(report: dict[RandovaniaGame, TrickDocumentation], webhook_url: str) -> None:
    embed = discord.Embed(
        title="Trick documentation report",
        description=(
            f"Generated with Randovania {randovania.VERSION}\n"
            f"Legend: :green_circle: Documented, :yellow_circle: Skipped, :red_circle: Undocumented"
        ),
    )

    for game, report in report.items():
        total = report.skipped + report.undocumented + report.documented
        if total == 0:
            embed.add_field(name=game.long_name, inline=False, value="No tricks")
            continue
        percent = int(((report.documented + report.skipped) / total) * 100)
        embed.add_field(
            name=game.long_name,
            inline=False,
            value=f"{percent: >3}% of {total}\n"
            f":green_circle: {report.documented} "
            f":yellow_circle: {report.skipped} "
            f":red_circle: {report.undocumented} ",
        )

    async with aiohttp.ClientSession() as session:
        webhook = discord.Webhook.from_url(webhook_url, session=session)
        await webhook.send(embed=embed)


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("reports_dir", type=Path, help="Where to store the usage reports")
    args = parser.parse_args()

    reports_dir: Path = args.reports_dir
    shutil.rmtree(reports_dir, ignore_errors=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    reports = {}

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
                os.fspath(reports_dir.joinpath(f"{game}.txt")),
            ],
            check=True,
            text=True,
        )

        undocumented = 0
        documented = 0
        skipped = 0

        with reports_dir.joinpath(f"{game}.txt").open() as usage_file:
            for line in usage_file:
                if line.startswith("- "):
                    if line.startswith("- (Documented)"):
                        documented += 1
                    elif line.startswith("- (Missing)"):
                        undocumented += 1
                    elif line.startswith("- (Skipped)"):
                        skipped += 1

        reports[game_enum] = TrickDocumentation(documented, undocumented, skipped)

    try:
        webhook_url = os.environ["WEBHOOK_URL"]
    except KeyError:
        return

    await post_report(reports, webhook_url)


if __name__ == "__main__":
    asyncio.run(main())
