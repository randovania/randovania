import re

import discord

import randovania
from randovania.games.game import RandovaniaGame
from randovania.gui.lib import preset_describer
from randovania.layout.permalink import Permalink

configuration: dict = None
client = discord.Client()

_PRETTY_GAME_NAME = {
    RandovaniaGame.PRIME1: "Metroid Prime 1",
    RandovaniaGame.PRIME2: "Metroid Prime 2: Echoes",
    RandovaniaGame.PRIME3: "Metroid Prime 3: Corruption",
}
possible_links_re = re.compile(r'([A-Za-z0-9-_]{8,})')


async def look_for_permalinks(message: str, channel: discord.TextChannel):
    for word in possible_links_re.finditer(message):
        try:
            permalink = Permalink.from_str(word.group(1))
        except ValueError:
            continue

        embed = discord.Embed(title=word.group(1),
                              description="{} player multiworld permalink".format(permalink.player_count))

        if permalink.player_count == 1:
            preset = permalink.get_preset(0)
            embed.description = "{} permalink for Randovania {}".format(_PRETTY_GAME_NAME[preset.game],
                                                                        randovania.VERSION)
            for category, items in preset_describer.describe(preset):
                embed.add_field(name=category, value="\n".join(items), inline=True)

        await channel.send(embed=embed)


@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return

    channel: discord.TextChannel = message.channel
    if configuration["channel_name_filter"] not in channel.name:
        return

    if message.guild.id != configuration["guild"]:
        return

    await look_for_permalinks(message.content, channel)


def run():
    global configuration
    configuration = randovania.get_configuration()["discord_bot"]
    client.run(configuration["token"])
