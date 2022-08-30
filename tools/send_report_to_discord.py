import argparse
import asyncio
from pathlib import Path

import discord

import randovania
from randovania.lib import json_lib


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config-path", type=Path, required=True)
    parser.add_argument("--report-title", type=str, required=True)
    parser.add_argument("--rdvgames-archive", type=Path, required=True)
    parser.add_argument("--report-path", type=Path, required=True)
    parser.add_argument("--channel", type=int, required=True)
    return parser


async def main():
    args = create_parser().parse_args()
    config_path: Path = args.config_path

    configuration = json_lib.read_path(config_path)
    bot_config = configuration["discord_bot"]

    report = json_lib.read_path(args.report_path)

    embed = discord.Embed(
        title=args.report_title,
        description=f"Generated with Randovania {randovania.VERSION}",
    )
    embed.add_field(name="Success count", value=str(report["seed_count"]))

    files = [
        discord.File(fp=args.rdvgames_archive),
        discord.File(fp=args.report_path, filename="report.json"),
    ]

    print("Preparing to connect with discord")
    client = discord.Client(intents=discord.Intents.default())
    print("Client created")
    try:
        await client.login(bot_config["token"])
        print("Client started")

        guild = await client.fetch_guild(bot_config["debug_guild"])
        print(f"Got guild {guild}")

        channel = await guild.fetch_channel(args.channel)
        print(f"Channel found: {channel}")
        assert isinstance(channel, discord.TextChannel)

        await channel.send(
            embed=embed,
            files=files,
        )
        print("Message sent.")
    finally:
        if not client.is_closed():
            await client.close()

    return 0


if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
