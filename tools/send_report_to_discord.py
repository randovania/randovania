import argparse
import asyncio
import traceback
from pathlib import Path

import discord

import randovania
from randovania.lib import json_lib


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config-path", type=Path, required=True)
    parser.add_argument("--title", type=str, required=True)
    parser.add_argument("--field", type=str, action='append',
                        help="Add a field to the embed. Title and value split by a :")
    parser.add_argument("--attach", type=Path, action='append')
    parser.add_argument("--channel", type=int, required=True)
    return parser


async def main():
    args = create_parser().parse_args()
    config_path: Path = args.config_path

    configuration = json_lib.read_path(config_path)
    bot_config = configuration["discord_bot"]

    embed = discord.Embed(
        title=args.title,
        description=f"Generated with Randovania {randovania.VERSION}",
    )
    for data in args.field:
        try:
            data = str(data)
            name, value = data.split(":", 1)

        except ValueError:
            traceback.print_exc()
            name = "Missing Title"
            value = data

        print(f"Adding field {name} with {value}")
        embed.add_field(name=name, value=value)

    files = [
        discord.File(fp=f)
        for f in args.attach
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
