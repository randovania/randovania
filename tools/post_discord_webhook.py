import asyncio
import datetime
import os
import subprocess
import urllib.parse

import aiohttp

from randovania import VERSION


async def post_to_discord():
    git_result = subprocess.run(["git", "show"], check=True, stdout=subprocess.PIPE, text=True).stdout.split("\n")
    commit_hash = git_result[0].split()[1]

    message = ""
    for line in git_result[4:]:
        if line.startswith("diff --git"):
            break
        else:
            message += line
            message += "\n"

    download_base = "https://bintray.com/randovania/randovania/download_file?file_path="
    windows_download_url = download_base + urllib.parse.quote(f"randovania-{VERSION}-windows.7z")

    webhook_data = {
        "embeds": [{
            "color": 0x2ecc71,
            "title": f"Randovania {VERSION}",
            "url": f"https://github.com/randovania/randovania/commit/{commit_hash}",
            "description": message.strip(),
            "fields": [
                {
                    "name": "Windows",
                    "value": f"[Download]({windows_download_url})",
                    "inline": True
                },
            ],
            "timestamp": datetime.datetime.now().isoformat()
        }]
    }
    webhook_url = os.environ["DISCORD_WEBHOOK"]
    async with aiohttp.ClientSession() as session:
        async with session.post(webhook_url, json=webhook_data, raise_for_status=True) as response:
            print(await response.text())


if __name__ == '__main__':
    asyncio.run(post_to_discord())
