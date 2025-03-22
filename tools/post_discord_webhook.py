# /// script
# dependencies = [
#   "aiohttp"
# ]
# ///
from __future__ import annotations

import argparse
import asyncio
import datetime
import os
import pprint
import subprocess
from pathlib import Path

import aiohttp


async def post_to_discord():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    args = parser.parse_args()

    version = args.version

    try:
        current_branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], check=True, stdout=subprocess.PIPE, text=True
        ).stdout.strip()
    except subprocess.SubprocessError:
        current_branch = "<Unknown Branch>"

    git_result = subprocess.run(["git", "show"], check=True, stdout=subprocess.PIPE, text=True).stdout.split("\n")
    commit_hash = git_result[0].split()[1]

    message = ""
    for line in git_result[4:]:
        if line.startswith("diff --git"):
            break
        else:
            message += line
            message += "\n"

    run_id = os.environ["GITHUB_RUN_ID"]
    org_name = "randovania"
    repo_name = "randovania"

    fields = [
        {
            "name": artifact.replace("Executable", "").replace("Randovania", "").strip(),
            "value": f"[Download](https://nightly.link/{org_name}/{repo_name}/"
            f"actions/runs/{run_id}/{artifact.replace(' ', '%20')}.zip)",
            "inline": True,
        }
        for artifact in [artifact.name for artifact in Path("packages").iterdir()]
        if artifact != "Python Package"
    ]

    message = message.strip()
    if len(message) > 4096:
        truncated = "\n<truncated due to size>"
        message = message[: 4090 - len(truncated)] + truncated

    webhook_data = {
        "embeds": [
            {
                "color": 0x2ECC71,
                "title": f"{current_branch} - Randovania {version}",
                "url": f"https://github.com/randovania/randovania/commit/{commit_hash}",
                "description": message.strip(),
                "fields": fields,
                "timestamp": datetime.datetime.now().isoformat(),
            }
        ]
    }
    pprint.pprint(webhook_data)

    webhook_url = os.environ["DISCORD_WEBHOOK"]
    async with aiohttp.ClientSession() as session:
        async with session.post(webhook_url, json=webhook_data, raise_for_status=True) as response:
            print(await response.text())


if __name__ == "__main__":
    asyncio.run(post_to_discord())
