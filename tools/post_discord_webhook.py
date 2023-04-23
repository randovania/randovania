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
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--artifact-dir", type=Path)
    group.add_argument("--version")
    args = parser.parse_args()

    if args.version is None:
        artifact_dir: Path = args.artifact_dir
        versions = {
            file.name.split("-")[1]
            for file in artifact_dir.glob("randovania-*")
        }
        if len(versions) != 1:
            raise ValueError(f"Found versions {sorted(versions)} in {artifact_dir}, expected just one")
        version = list(versions)[0]
    else:
        version = args.version

    print(version)

    try:
        current_branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                                        check=True, stdout=subprocess.PIPE, text=True).stdout.strip()
    except Exception:
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
            "inline": True
        }
        for artifact in os.listdir("packages")
    ]

    webhook_data = {
        "embeds": [{
            "color": 0x2ecc71,
            "title": f"{current_branch} - Randovania {version}",
            "url": f"https://github.com/randovania/randovania/commit/{commit_hash}",
            "description": message.strip(),
            "fields": fields,
            "timestamp": datetime.datetime.now().isoformat()
        }]
    }
    pprint.pprint(webhook_data)

    webhook_url = os.environ["DISCORD_WEBHOOK"]
    async with aiohttp.ClientSession() as session:
        async with session.post(webhook_url, json=webhook_data, raise_for_status=True) as response:
            print(await response.text())


if __name__ == '__main__':
    asyncio.run(post_to_discord())
