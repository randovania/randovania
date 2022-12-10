import argparse
import asyncio
import traceback
from pathlib import Path

import aiohttp
import discord

import randovania


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", type=str, required=True)
    parser.add_argument("--field", type=str, action='append', default=[],
                        help="Add a field to the embed. Title and value split by a :")
    parser.add_argument("--attach", type=Path, action='append', default=[])
    parser.add_argument("--webhook-url", type=str, required=True)
    return parser


async def main():
    args = create_parser().parse_args()
    webhook_url: str = args.webhook_url

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

    async with aiohttp.ClientSession() as session:
        webhook = discord.Webhook.from_url(webhook_url, session=session)
        await webhook.send(
            embed=embed,
            files=files,
        )
        print("Message sent.")

    return 0


if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
